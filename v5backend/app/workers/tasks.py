from __future__ import annotations
import hashlib
import mimetypes
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, text
from app.db.session import SessionLocal
from app.db import models
from app.services.storage import get_object
from app.services.extractor import extract_text
from app.services.chunker import simple_chunk, section_aware_chunks
from app.services.embeddings import embed_chunks
from app.services.llm import extract_facts_with_cascade
from app.monitoring.metrics import EXTRACT_LATENCY, EMBED_LATENCY, LLM_LATENCY, AGENT_CONFIDENCE, AGENT_FALLBACKS
from app.core.config import settings
from app.core.logging import get_logger
from .celery_app import celery_app

# Agentic pipeline imports
from app.agents.extract_map import map_extract_chunks
from app.agents.merge_normalize import merge_partial_facts, to_validated_model
from app.agents.qa_consistency import basic_consistency_checks
from app.agents.summarize_score import generate_summaries, compute_scores

log = get_logger("worker")


def _detect_mime(key: str) -> str:
    ext = key.split(".")[-1].lower()
    if ext == "pdf":
        return "application/pdf"
    if ext == "docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return mimetypes.guess_type(key)[0] or "application/octet-stream"


def _ensure_chunk_section_column(session: Session) -> None:
    try:
        session.execute(text("""
            ALTER TABLE resume_chunks
            ADD COLUMN IF NOT EXISTS section VARCHAR(64) NOT NULL DEFAULT 'unknown';
        """))
        session.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_class c WHERE c.relname = 'resume_chunks_section_idx'
                ) THEN
                    CREATE INDEX resume_chunks_section_idx ON resume_chunks(section);
                END IF;
            END $$;
        """))
        session.commit()
    except Exception:
        session.rollback()
        # Non-fatal; inserts will still work if column already exists
        pass


@celery_app.task(name="process_resume_io")
def process_resume_io(resume_id: str, key: str, original_filename: str, size: int):
    log.info("task_start", task="process_resume_io", resume_id=resume_id, key=key, size=size)
    with SessionLocal() as session:
        res = session.get(models.Resume, resume_id)
        if not res:
            log.warning("resume_missing", resume_id=resume_id)
            return False
        
        # Ensure the resume has the s3_key stored
        if not res.s3_key:
            res.s3_key = key
            session.commit()
            log.info("updated_missing_s3_key", resume_id=resume_id, s3_key=key)
        
        try:
            data = get_object(settings.S3_BUCKET, key)
        except FileNotFoundError:
            log.error("s3_file_missing", resume_id=resume_id, key=key)
            res.status = "failed"
            res.error_message = f"File not found in storage: {key}"
            session.commit()
            # Mark task as failed but don't crash the worker
            raise FileNotFoundError(f"S3 object not found: s3://{settings.S3_BUCKET}/{key}")
        except Exception as e:
            log.error("s3_access_error", resume_id=resume_id, key=key, error=str(e))
            res.status = "failed"
            res.error_message = f"Storage access error: {str(e)}"
            session.commit()
            # Re-raise the original exception for proper error handling
            raise
            
        mime = _detect_mime(key)
        # Hash for dedupe
        content_hash = hashlib.sha256(data).hexdigest()
        existing = session.scalar(select(models.Resume).where(models.Resume.content_hash == content_hash, models.Resume.id != res.id))
        if existing:
            res.status = "duplicate"
            session.commit()
            log.info("resume_duplicate", resume_id=resume_id, duplicate_of=str(existing.id))
            return str(existing.id)

        res.mime = mime
        res.size = size
        res.content_hash = content_hash
        res.status = "processing"
        res.error_message = None  # Clear any previous error
        session.commit()

        try:
            with EXTRACT_LATENCY.time():
                text, _ = extract_text(mime, data)
        except ValueError as e:
            log.error("text_extraction_error", resume_id=resume_id, error=str(e))
            res.status = "failed"
            res.error_message = f"Text extraction failed: {str(e)}"
            session.commit()
            return False
        except Exception as e:
            log.error("unexpected_extraction_error", resume_id=resume_id, error=str(e))
            res.status = "failed"
            res.error_message = f"Unexpected error during text extraction: {str(e)}"
            session.commit()
            return False
            
        if not text or not text.strip():
            log.warning("no_text_extracted", resume_id=resume_id)
            res.status = "failed"
            res.error_message = "No text could be extracted from the document"
            session.commit()
            return False
            
        session.add(models.ResumeText(resume_id=res.id, full_text=text))
        session.commit()
        log.info("text_extracted", resume_id=resume_id, chars=len(text))

        # Ensure schema supports sections
        _ensure_chunk_section_column(session)

        # Section-aware chunking
        sec_chunks = section_aware_chunks(text)
        chunks = [c["text"] for c in sec_chunks]
        sections = [str(c.get("section") or "unknown") for c in sec_chunks]
        log.info("chunks_created", resume_id=resume_id, count=len(chunks))
        # Queue embedding stage with sections and high priority for immediate processing
        celery_app.signature("embed_chunks_io", args=[str(res.id), chunks, sections]).apply_async(queue="io", priority=9)
        log.info("task_enqueue", next_task="embed_chunks_io", resume_id=resume_id, priority="high")
        return str(res.id)


@celery_app.task(name="embed_chunks_io")
def embed_chunks_io(resume_id: str, chunks: list[str], sections: list[str] | None = None):
    import asyncio
    import json
    log.info("task_start", task="embed_chunks_io", resume_id=resume_id, count=len(chunks))
    from app.services.embeddings import embed_chunks as embed_async
    from app.db.models import has_vector_support
    
    vectors = asyncio.run(embed_async(chunks))

    with SessionLocal() as session:
        vector_support = has_vector_support()
        
        for idx, (text, vec) in enumerate(zip(chunks, vectors)):
            sec = (sections[idx] if sections and idx < len(sections) else "unknown")
            
            # Handle embedding serialization based on vector support
            if vector_support:
                # Store as vector type when pgvector available
                embedding_value = vec
            else:
                # Store as JSON string when falling back to text column
                embedding_value = json.dumps(vec) if vec else None
                
            session.add(models.ResumeChunk(
                resume_id=resume_id, 
                idx=idx, 
                text=text, 
                embedding=embedding_value, 
                section=sec
            ))
        session.commit()
    # Queue multi-pass LLM chain immediately with high priority
    celery_app.signature("analyze_resume_llm", args=[resume_id]).apply_async(queue="llm", priority=9)
    log.info("task_enqueue", next_task="analyze_resume_llm", resume_id=resume_id, priority="high")
    return True


# --- Multi-pass analysis tasks ---

@celery_app.task(name="analyze_resume_pass1_llm")
def analyze_resume_pass1_llm(resume_id: str):
    import asyncio
    log.info("task_start", task="analyze_resume_pass1_llm", resume_id=resume_id)
    with SessionLocal() as session:
        res = session.get(models.Resume, resume_id)
        if not res or not res.text:
            log.warning("resume_text_missing", resume_id=resume_id)
            return False
        # Gather limited chunk texts for speed
        chunks = session.query(models.ResumeChunk).where(models.ResumeChunk.resume_id == resume_id).order_by(models.ResumeChunk.idx.asc()).limit(20).all()
        chunk_texts = [c.text for c in chunks]
        with LLM_LATENCY.time():
            partials = asyncio.run(map_extract_chunks(chunk_texts, max_chunks=20))
        merged = merge_partial_facts(partials)
        facts_model = to_validated_model(merged)
        facts = facts_model.model_dump()
        # Short summary only
        try:
            summaries = asyncio.run(generate_summaries({**facts, "experience": (facts.get("experience") or [])[:2]}))
            facts["summary_short"] = summaries.get("summary_short", "")
        except Exception:
            pass
        scores = compute_scores(facts)
        pipeline = "agentic_p1"
        # Save version
        session.add(models.ResumeFactsVersion(resume_id=res.id, pass_no=1, pipeline=pipeline, extracted_json=facts, scores=scores))
        # Upsert current snapshot
        existing = session.get(models.ResumeFacts, resume_id)
        if existing:
            existing.extracted_json = facts
            existing.scores = {**(existing.scores or {}), **scores, "pipeline": pipeline, "pass": 1}
        else:
            session.add(models.ResumeFacts(resume_id=resume_id, extracted_json=facts, scores={**scores, "pipeline": pipeline, "pass": 1}))
        res.status = "complete_p1"
        session.commit()
    try:
        AGENT_CONFIDENCE.observe(float(scores.get("confidence", 0.0)))
    except Exception:
        pass
    # Enqueue pass2 immediately with high priority
    celery_app.signature("analyze_resume_pass2_llm", args=[resume_id]).apply_async(queue="llm", priority=9)
    return True


@celery_app.task(name="analyze_resume_pass2_llm")
def analyze_resume_pass2_llm(resume_id: str):
    import asyncio
    log.info("task_start", task="analyze_resume_pass2_llm", resume_id=resume_id)
    with SessionLocal() as session:
        res = session.get(models.Resume, resume_id)
        if not res or not res.text:
            log.warning("resume_text_missing", resume_id=resume_id)
            return False
        chunks = session.query(models.ResumeChunk).where(models.ResumeChunk.resume_id == resume_id).order_by(models.ResumeChunk.idx.asc()).all()
        chunk_texts = [c.text for c in chunks]
        with LLM_LATENCY.time():
            partials = asyncio.run(map_extract_chunks(chunk_texts))
        merged = merge_partial_facts(partials)
        facts_model = to_validated_model(merged)
        facts = facts_model.model_dump()
        summaries = asyncio.run(generate_summaries(facts))
        if summaries.get("summary_short"):
            facts["summary_short"] = summaries["summary_short"]
        if summaries.get("summary_detailed"):
            facts["summary_detailed"] = summaries["summary_detailed"]
        qa = basic_consistency_checks(facts)
        scores = compute_scores(facts)
        scores["qa_ok"] = qa.get("ok", True)
        scores["qa_issues"] = len(qa.get("issues", []))
        pipeline = "agentic_p2"
        # Fallback cascade if low confidence
        if scores.get("confidence", 0.0) <= 0.6:
            full_text = res.text.full_text
            try:
                with LLM_LATENCY.time():
                    fb_data, fb_conf = asyncio.run(extract_facts_with_cascade(full_text))
                merged2 = merge_partial_facts([{"data": facts}, {"data": fb_data}])
                facts = to_validated_model(merged2).model_dump()
                summaries = asyncio.run(generate_summaries(facts))
                if summaries.get("summary_short"):
                    facts["summary_short"] = summaries["summary_short"]
                if summaries.get("summary_detailed"):
                    facts["summary_detailed"] = summaries["summary_detailed"]
                scores = compute_scores(facts)
                scores["fallback_confidence"] = fb_conf
                try:
                    AGENT_FALLBACKS.inc()
                except Exception:
                    pass
            except Exception as e:
                log.warning("fallback_failed", resume_id=resume_id, error=str(e))
        # Save version
        session.add(models.ResumeFactsVersion(resume_id=res.id, pass_no=2, pipeline=pipeline, extracted_json=facts, scores=scores))
        existing = session.get(models.ResumeFacts, resume_id)
        if existing:
            existing.extracted_json = facts
            existing.scores = {**(existing.scores or {}), **scores, "pipeline": pipeline, "pass": 2}
        else:
            session.add(models.ResumeFacts(resume_id=resume_id, extracted_json=facts, scores={**scores, "pipeline": pipeline, "pass": 2}))
        res.status = "complete_p2"
        session.commit()
    try:
        AGENT_CONFIDENCE.observe(float(scores.get("confidence", 0.0)))
    except Exception:
        pass
    # Enqueue pass3 immediately for fastest processing with high priority
    celery_app.signature("analyze_resume_pass3_llm", args=[resume_id]).apply_async(queue="llm", priority=9)
    return True


@celery_app.task(name="analyze_resume_pass3_llm")
def analyze_resume_pass3_llm(resume_id: str):
    import asyncio
    log.info("task_start", task="analyze_resume_pass3_llm", resume_id=resume_id)
    with SessionLocal() as session:
        res = session.get(models.Resume, resume_id)
        if not res or not res.text:
            log.warning("resume_text_missing", resume_id=resume_id)
            return False
        # Final enrichment could be added here; for now recompute summaries to ensure completeness
        existing = session.get(models.ResumeFacts, resume_id)
        facts = (existing.extracted_json if existing else {}) or {}
        try:
            summaries = asyncio.run(generate_summaries(facts))
            if summaries.get("summary_short"):
                facts["summary_short"] = summaries["summary_short"]
            if summaries.get("summary_detailed"):
                facts["summary_detailed"] = summaries["summary_detailed"]
        except Exception:
            pass
        qa = basic_consistency_checks(facts)
        scores = compute_scores(facts)
        scores["qa_ok"] = qa.get("ok", True)
        scores["qa_issues"] = len(qa.get("issues", []))
        pipeline = "agentic_p3"
        session.add(models.ResumeFactsVersion(resume_id=res.id, pass_no=3, pipeline=pipeline, extracted_json=facts, scores=scores))
        if existing:
            existing.extracted_json = facts
            existing.scores = {**(existing.scores or {}), **scores, "pipeline": pipeline, "pass": 3}
        else:
            session.add(models.ResumeFacts(resume_id=resume_id, extracted_json=facts, scores={**scores, "pipeline": pipeline, "pass": 3}))
        res.status = "complete"
        session.commit()
    try:
        AGENT_CONFIDENCE.observe(float(scores.get("confidence", 0.0)))
    except Exception:
        pass
    log.info("task_done", task="analyze_resume_pass3_llm", resume_id=resume_id, confidence=float(scores.get("confidence", 0.0)), pipeline=pipeline)
    return True


@celery_app.task(name="analyze_resume_llm")
def analyze_resume_llm(resume_id: str):
    """Backwards-compatible entry: schedule 3-pass chain with high priority."""
    log.info("task_start", task="analyze_resume_llm", resume_id=resume_id)
    # Kick off pass1 immediately with high priority for faster processing
    celery_app.signature("analyze_resume_pass1_llm", args=[resume_id]).apply_async(queue="llm", priority=9)
    log.info("task_enqueue", next_task="analyze_resume_pass1_llm", resume_id=resume_id, priority="high")
    return True


@celery_app.task(name="monitor_resume_status")
def monitor_resume_status():
    """Background task to monitor and auto-recover stuck resumes"""
    from app.services.status_monitor import StatusMonitor
    
    log.info("task_start", task="monitor_resume_status")
    
    try:
        with StatusMonitor() as monitor:
            # Find and recover stuck resumes - much more aggressive timing
            stuck_resumes = monitor.find_stuck_resumes(minutes_threshold=2)  # 2 minutes threshold (was 15 minutes)
            ready_resumes = monitor.find_ready_for_analysis()
            
            recovered = 0
            triggered = 0
            errors = []
            
            # Recover stuck resumes
            for status in stuck_resumes:
                try:
                    if monitor.trigger_analysis(status.id):
                        recovered += 1
                        log.info("monitor_recovered_stuck", resume_id=status.id, stage=status.analysis_stage)
                    else:
                        errors.append(f"Failed to recover {status.id}")
                except Exception as e:
                    errors.append(f"Error recovering {status.id}: {str(e)}")
                    log.error("monitor_recover_error", resume_id=status.id, error=str(e))
            
            # Trigger analysis for ready resumes
            for status in ready_resumes:
                try:
                    if monitor.trigger_analysis(status.id):
                        triggered += 1
                        log.info("monitor_triggered_ready", resume_id=status.id)
                    else:
                        errors.append(f"Failed to trigger {status.id}")
                except Exception as e:
                    errors.append(f"Error triggering {status.id}: {str(e)}")
                    log.error("monitor_trigger_error", resume_id=status.id, error=str(e))
            
            # Log summary
            log.info("monitor_complete", 
                    stuck_found=len(stuck_resumes), 
                    ready_found=len(ready_resumes),
                    recovered=recovered, 
                    triggered=triggered, 
                    errors=len(errors))
            
            return {
                "stuck_found": len(stuck_resumes),
                "ready_found": len(ready_resumes),
                "recovered": recovered,
                "triggered": triggered,
                "errors": errors
            }
            
    except Exception as e:
        log.error("monitor_resume_status_failed", error=str(e), exc_info=True)
        return {"error": str(e)}


@celery_app.task(name="resume_health_check")
def resume_health_check():
    """Comprehensive health check of resume processing system"""
    from app.services.status_monitor import StatusMonitor
    from app.db.session import SessionLocal
    from app.db import models
    from sqlalchemy import select, func, text
    
    log.info("task_start", task="resume_health_check")
    
    try:
        with StatusMonitor() as monitor:
            # Get system stats
            stats = monitor.get_system_stats()
            
            # Additional health checks
            with SessionLocal() as session:
                # Check for orphaned chunks (chunks without resumes)
                orphaned_chunks = session.scalar(
                    select(func.count(models.ResumeChunk.id))
                    .outerjoin(models.Resume, models.ResumeChunk.resume_id == models.Resume.id)
                    .where(models.Resume.id.is_(None))
                ) or 0
                
                # Check for orphaned texts
                orphaned_texts = session.scalar(
                    select(func.count(models.ResumeText.resume_id))
                    .outerjoin(models.Resume, models.ResumeText.resume_id == models.Resume.id)
                    .where(models.Resume.id.is_(None))
                ) or 0
                
                # Check for orphaned facts
                orphaned_facts = session.scalar(
                    select(func.count(models.ResumeFacts.resume_id))
                    .outerjoin(models.Resume, models.ResumeFacts.resume_id == models.Resume.id)
                    .where(models.Resume.id.is_(None))
                ) or 0
                
                # Check database size
                try:
                    db_size = session.scalar(
                        text("SELECT pg_size_pretty(pg_database_size(current_database()))")
                    )
                except Exception:
                    db_size = "unknown"
                
                # Check table sizes
                try:
                    table_sizes = {}
                    for table in ["resumes", "resume_text", "resume_chunks", "resume_facts", "resume_facts_versions"]:
                        size = session.scalar(
                            text(f"SELECT pg_size_pretty(pg_total_relation_size('{table}'))")
                        )
                        table_sizes[table] = size
                except Exception:
                    table_sizes = {}
            
            health_info = {
                **stats,
                "orphaned_data": {
                    "chunks": orphaned_chunks,
                    "texts": orphaned_texts,
                    "facts": orphaned_facts
                },
                "database": {
                    "size": db_size,
                    "table_sizes": table_sizes
                },
                "health_score": "good" if stats.get("stuck_count", 0) == 0 and orphaned_chunks == 0 else "warning"
            }
            
            log.info("health_check_complete", 
                    total_resumes=stats.get("total_resumes", 0),
                    completion_rate=stats.get("analysis_stats", {}).get("completion_rate", 0),
                    stuck_count=stats.get("stuck_count", 0),
                    health_score=health_info["health_score"])
            
            return health_info
            
    except Exception as e:
        log.error("resume_health_check_failed", error=str(e), exc_info=True)
        return {"error": str(e), "health_score": "error"}
