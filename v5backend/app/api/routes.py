from __future__ import annotations
import json
import uuid
import asyncio
import time
from datetime import datetime
from sqlalchemy import text
from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from app.schemas.resume import UploadResponse, SearchRequest, MatchRequest, ChatRequest
from app.core.config import settings
from app.core.logging import get_logger
from app.services.storage import upload_to_tmp, promote_tmp_to_resumes
from app.workers.celery_app import celery_app
from app.db.session import SessionLocal
from app.db import models
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.services.embeddings import embed_text
from app.services.retriever import hybrid_search, build_context_from_chunks
from app.services.llm import rag_chat_stream
from app.core.preflight import db_status_snapshot, redis_status_snapshot, s3_status_snapshot
from app.services.retriever import hybrid_search_adv

bp = Blueprint("api", __name__)
log = get_logger("api")


@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@bp.route("/debug/config", methods=["GET"])
def debug_config():
    """Debug endpoint to check configuration (exclude sensitive data)"""
    from app.core.config import settings
    
    return jsonify({
        "s3_endpoint": settings.S3_ENDPOINT,
        "s3_bucket": settings.S3_BUCKET,
        "s3_bucket_tmp": settings.S3_BUCKET_TMP,
        "s3_region": settings.S3_REGION,
        "s3_path_style": settings.S3_PATH_STYLE,
        "s3_access_key_set": bool(settings.S3_ACCESS_KEY),
        "s3_secret_key_set": bool(settings.S3_SECRET_KEY),
        "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
        "allowed_exts": settings.ALLOWED_EXTS,
        "env": settings.ENV,
    })


@bp.route("/debug/s3test", methods=["POST"])
def debug_s3_test():
    """Debug endpoint to test S3 operations"""
    try:
        from app.services.storage import get_s3_client
        s3 = get_s3_client()
        
        # Test basic connectivity
        buckets_response = s3.list_buckets()
        bucket_names = [b['Name'] for b in buckets_response.get('Buckets', [])]
        
        # Test bucket access
        bucket_status = {}
        for bucket in [settings.S3_BUCKET, settings.S3_BUCKET_TMP]:
            try:
                s3.head_bucket(Bucket=bucket)
                bucket_status[bucket] = "accessible"
            except Exception as e:
                bucket_status[bucket] = f"error: {str(e)}"
        
        return jsonify({
            "s3_reachable": True,
            "available_buckets": bucket_names,
            "target_bucket_status": bucket_status,
            "test_passed": True
        })
        
    except Exception as e:
        return jsonify({
            "s3_reachable": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "test_passed": False
        }), 500


@bp.route("/debug/migrate", methods=["POST"])
def debug_migrate():
    """Manual migration trigger for Railway deployment"""
    try:
        log.info("manual_migration_requested")
        
        # Try to run Alembic migration
        try:
            try:
                from alembic.config import Config
                from alembic import command
                ALEMBIC_AVAILABLE = True
            except ImportError:
                ALEMBIC_AVAILABLE = False
            
            if ALEMBIC_AVAILABLE:
                import os
                
                # Get the alembic config file path
                alembic_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'alembic.ini')
                if not os.path.exists(alembic_cfg_path):
                    alembic_cfg_path = '/app/alembic.ini'  # Railway deployment path
                
                if os.path.exists(alembic_cfg_path):
                    alembic_cfg = Config(alembic_cfg_path)
                    command.upgrade(alembic_cfg, "head")
                    migration_result = "success"
                    migration_error = None
                    log.info("manual_migration_success")
                else:
                    migration_result = "config_not_found"
                    migration_error = f"Alembic config not found at {alembic_cfg_path}"
                    log.warning("alembic_config_not_found", path=alembic_cfg_path)
            else:
                migration_result = "alembic_not_available"
                migration_error = "Alembic package not available"
                log.warning("alembic_package_missing")
                
        except Exception as e:
            migration_result = "failed"
            migration_error = str(e)
            log.error("manual_migration_failed", error=str(e))
        
        # Check if s3_key column exists now
        s3_key_exists = False
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT s3_key FROM resumes LIMIT 1"))
                s3_key_exists = True
        except Exception as e:
            log.info("s3_key_column_check", exists=False, error=str(e))
        
        # Check current migration version
        current_version = None
        try:
            with SessionLocal() as session:
                result = session.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                current_version = result[0] if result else None
        except Exception as e:
            log.warning("migration_version_check_failed", error=str(e))
        
        return jsonify({
            "migration_result": migration_result,
            "migration_error": migration_error,
            "s3_key_column_exists": s3_key_exists,
            "current_migration_version": current_version,
            "expected_version": "20250810_04",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        log.error("debug_migrate_error", error=str(e))
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


@bp.route("/debug/migrate-sql", methods=["POST"])
def debug_migrate_sql():
    """Manual SQL-based migration as fallback"""
    try:
        log.info("manual_sql_migration_requested")
        
        results = []
        
        with SessionLocal() as session:
            # Check if s3_key column exists
            try:
                session.execute(text("SELECT s3_key FROM resumes LIMIT 1"))
                results.append("s3_key column already exists")
                s3_key_exists = True
            except Exception:
                s3_key_exists = False
                
                # Try to add s3_key column
                try:
                    session.execute(text("ALTER TABLE resumes ADD COLUMN s3_key VARCHAR(512)"))
                    session.commit()
                    results.append("✅ Added s3_key column")
                except Exception as e:
                    results.append(f"❌ Failed to add s3_key column: {str(e)}")
                
                # Try to add index
                try:
                    session.execute(text("CREATE INDEX IF NOT EXISTS ix_resumes_s3_key ON resumes(s3_key)"))
                    session.commit()
                    results.append("✅ Added s3_key index")
                except Exception as e:
                    results.append(f"❌ Failed to add s3_key index: {str(e)}")
            
            # Check if error_message column exists
            try:
                session.execute(text("SELECT error_message FROM resumes LIMIT 1"))
                results.append("error_message column already exists")
            except Exception:
                # Try to add error_message column
                try:
                    session.execute(text("ALTER TABLE resumes ADD COLUMN error_message TEXT"))
                    session.commit()
                    results.append("✅ Added error_message column")
                except Exception as e:
                    results.append(f"❌ Failed to add error_message column: {str(e)}")
            
            # Update alembic version if possible
            try:
                # Check if alembic_version table exists
                session.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                # Update to latest version
                session.execute(text("UPDATE alembic_version SET version_num = '20250810_04'"))
                session.commit()
                results.append("✅ Updated alembic version to 20250810_04")
            except Exception as e:
                results.append(f"⚠️ Could not update alembic version: {str(e)}")
        
        # Final check
        try:
            with SessionLocal() as session:
                session.execute(text("SELECT s3_key, error_message FROM resumes LIMIT 1"))
                final_check = "✅ Both columns accessible"
        except Exception as e:
            final_check = f"❌ Final check failed: {str(e)}"
        
        results.append(final_check)
        
        return jsonify({
            "migration_type": "sql_manual",
            "results": results,
            "success": "✅" in final_check,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        log.error("debug_migrate_sql_error", error=str(e))
        return jsonify({
            "error": str(e),
            "error_type": type(e).__name__
        }), 500


@bp.route("/metrics", methods=["GET"])
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@bp.route("/healthz/details", methods=["GET"])
def health_details():
    # Non-mutating one-shot snapshot for dashboards and checks
    db = db_status_snapshot()
    rd = redis_status_snapshot()
    s3 = s3_status_snapshot()
    overall = bool(db.get("reachable") and rd.get("reachable") and s3.get("reachable"))
    payload = {
        "ok": overall,
        "db": db,
        "redis": rd,
        "s3": s3,
        "env": settings.ENV,
        "ts": int(time.time()),
    }
    return jsonify(payload)


@bp.route("/healthz/stream", methods=["GET"])
def health_stream():
    # Server-Sent Events stream; updates every 2s, flush-friendly
    interval = float(request.args.get("interval", 2))

    @stream_with_context
    def _gen():
        while True:
            try:
                db = db_status_snapshot()
                rd = redis_status_snapshot()
                s3 = s3_status_snapshot()
                payload = {
                    "ok": bool(db.get("reachable") and rd.get("reachable") and s3.get("reachable")),
                    "db": db,
                    "redis": rd,
                    "s3": s3,
                    "ts": int(time.time()),
                }
                yield f"data: {json.dumps(payload)}\n\n"
                time.sleep(interval)
            except GeneratorExit:
                break
            except Exception as e:
                # Send error event and continue
                ev = {"ok": False, "error": str(e), "ts": int(time.time())}
                yield f"event: error\ndata: {json.dumps(ev)}\n\n"
                time.sleep(interval)

    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "text/event-stream",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }
    return Response(_gen(), headers=headers)


@bp.route("/resumes/upload", methods=["POST"])
def upload():
    try:
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "No files"}), 400

        items: list[dict] = []
        upload_errors: list[str] = []
        
        for f in files:
            try:
                items.extend(upload_to_tmp(f))
                log.info("upload_tmp_success", filename=getattr(f, 'filename', None))
            except Exception as e:
                error_msg = f"Failed to upload {getattr(f, 'filename', 'unknown')}: {str(e)}"
                log.warning("upload_tmp_failed", filename=getattr(f, 'filename', None), error=str(e))
                upload_errors.append(error_msg)
                continue

        if not items:
            error_detail = "All file uploads failed"
            if upload_errors:
                error_detail += f": {'; '.join(upload_errors)}"
            log.error("upload_all_failed", errors=upload_errors)
            return jsonify({"error": error_detail}), 400

        # Promote to final bucket
        try:
            final_items = promote_tmp_to_resumes(items)
            log.info("promote_success", count=len(final_items))
        except Exception as e:
            log.error("promote_failed", error=str(e), items_count=len(items))
            return jsonify({"error": f"Failed to promote files to storage: {str(e)}"}), 500

        ids: list[str] = []
        db_errors: list[str] = []
        
        try:
            with SessionLocal() as session:
                for it in final_items:
                    try:
                        rid = uuid.uuid4()
                        
                        # Create resume with backward compatibility for s3_key column
                        resume_data = {
                            "id": rid,
                            "original_filename": str(it.get("original_filename") or it["key"]),
                            "mime": "",
                            "size": int(it.get("size") or 0),
                            "content_hash": "",
                            "status": "queued",
                        }
                        
                        # Only add s3_key if the column exists (for backward compatibility)
                        try:
                            # Check if s3_key column exists by attempting to query it
                            session.execute(text("SELECT s3_key FROM resumes LIMIT 1"))
                            # If no exception, column exists
                            resume_data["s3_key"] = str(it["key"])
                            log.info("s3_key_column_available", resume_id=str(rid))
                        except Exception as e:
                            # Column doesn't exist, use content_hash as fallback storage for key
                            resume_data["content_hash"] = str(it["key"])  # Store S3 key in content_hash as fallback
                            log.warning("s3_key_column_missing", resume_id=str(rid), fallback="content_hash", error=str(e))
                        
                        resume = models.Resume(**resume_data)
                        session.add(resume)
                        session.commit()
                        ids.append(str(rid))
                        
                        # Enqueue processing with this known ID
                        try:
                            celery_app.signature("process_resume_io", args=[str(rid), it["key"], resume.original_filename, resume.size]).apply_async(queue="io")
                            log.info("resume_enqueued", resume_id=str(rid), key=it["key"], size=resume.size)
                        except Exception as e:
                            log.warning("celery_enqueue_failed", resume_id=str(rid), error=str(e))
                            # Continue even if celery enqueue fails - the resume is still in the DB
                            
                    except Exception as e:
                        error_msg = f"Failed to save resume {it.get('original_filename', 'unknown')}: {str(e)}"
                        log.error("db_save_failed", item=it, error=str(e))
                        db_errors.append(error_msg)
                        continue
                        
        except Exception as e:
            log.error("db_session_failed", error=str(e))
            return jsonify({"error": f"Database error: {str(e)}"}), 500

        if not ids:
            error_detail = "All database saves failed"
            if db_errors:
                error_detail += f": {'; '.join(db_errors)}"
            return jsonify({"error": error_detail}), 500

        # Return success with any partial errors noted
        response_data = UploadResponse(ids=ids).dict()
        if upload_errors or db_errors:
            response_data["warnings"] = upload_errors + db_errors
            
        log.info("upload_complete", ids_count=len(ids), upload_errors=len(upload_errors), db_errors=len(db_errors))
        return jsonify(response_data)
        
    except Exception as e:
        log.error("upload_unexpected_error", error=str(e), error_type=type(e).__name__)
        return jsonify({"error": f"Unexpected error during upload: {str(e)}"}), 500


@bp.route("/resumes/<rid>", methods=["GET"])
def get_resume(rid: str):
    with SessionLocal() as session:
        res = session.get(models.Resume, rid)
        if not res:
            return jsonify({"error": "not found"}), 404
        facts = session.get(models.ResumeFacts, rid)
        return jsonify({
            "id": str(res.id),
            "original_filename": res.original_filename,
            "mime": res.mime,
            "size": res.size,
            "s3_key": res.s3_key,
            "status": res.status,
            "error_message": res.error_message,
            "extracted_json": facts.extracted_json if facts else None,
            "scores": facts.scores if facts else None,
        })


@bp.route("/search", methods=["POST"])
def search():
    from app.services.vector_support import detect_vector_support
    
    req = SearchRequest(**request.json)
    with SessionLocal() as session:
        try:
            vec = asyncio.run(embed_text(req.query))
        except Exception as e:
            log.warning("embedding_failed", error=str(e), query=req.query)
            # Fallback to empty vector if embedding fails
            vec = []
            
        # Optional filter by sections
        sections = None
        if isinstance(request.json, dict) and request.json.get("sections"):
            sections = [str(s).lower() for s in request.json.get("sections")]
            
        # Check vector support for informative logging
        vector_available = detect_vector_support()
        log.info("search_start", query=req.query, vector_support=vector_available, sections=sections)
        
        try:
            # Use advanced hybrid retrieval for better ranking
            results = hybrid_search_adv(session, req.query, vec, top_k=req.page_size, per_resume_limit=settings.RETRIEVAL_PER_RESUME_LIMIT, sections=sections)
            items = [
                {
                    "resume_id": str(ch.resume_id),
                    "idx": ch.idx,
                    "section": getattr(ch, "section", "unknown"),
                    "preview": ch.text[:300],
                    "score": score,
                }
                for ch, score in results
            ]
            log.info("search", query=req.query, count=len(items), top_k=req.top_k, page=req.page, vector_support=vector_available)
            return jsonify({
                "page": req.page,
                "page_size": req.page_size,
                "count": len(items),
                "results": items,
                "vector_support": vector_available,
            })
        except Exception as e:
            log.error("search_failed", error=str(e), query=req.query)
            return jsonify({"error": "Search failed", "details": str(e)}), 500


@bp.route("/match", methods=["POST"])
def match():
    from app.services.vector_support import detect_vector_support
    
    req = MatchRequest(**request.json)
    with SessionLocal() as session:
        try:
            vec = asyncio.run(embed_text(req.job_description))
        except Exception as e:
            log.warning("embedding_failed", error=str(e), job_description=req.job_description[:100])
            # Fallback to empty vector if embedding fails
            vec = []
            
        vector_available = detect_vector_support()
        log.info("match_start", vector_support=vector_available, job_desc_preview=req.job_description[:100])
        
        try:
            results = hybrid_search_adv(session, req.job_description, vec, top_k=req.top_k, per_resume_limit=settings.RETRIEVAL_PER_RESUME_LIMIT)
            # Group by resume_id
            scored: dict[str, float] = {}
            for ch, score in results:
                rid = str(ch.resume_id)
                scored[rid] = scored.get(rid, 0.0) + (1.0 / (1.0 + score))
            ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)
            log.info("match", count=len(ranked), top_k=req.top_k, vector_support=vector_available)
            return jsonify({
                "matches": [{"resume_id": rid, "score": s} for rid, s in ranked],
                "vector_support": vector_available,
            })
        except Exception as e:
            log.error("match_failed", error=str(e), job_desc_preview=req.job_description[:100])
            return jsonify({"error": "Match failed", "details": str(e)}), 500


def _emit_tool_event(name: str, payload: dict) -> str:
    # Avoid nested braces inside an f-string expression to prevent parser issues
    data = {"tool": name}
    try:
        if payload:
            data.update(payload)
    except Exception:
        pass
    return "event: tool\ndata: " + json.dumps(data) + "\n\n"


@bp.route("/chat", methods=["POST"])
def chat():
    from app.services.vector_support import detect_vector_support
    
    req = ChatRequest(**request.json)
    query = req.message
    with SessionLocal() as session:
        try:
            vec = asyncio.run(embed_text(query))
        except Exception as e:
            log.warning("embedding_failed", error=str(e), query=query[:100])
            # Fallback to empty vector if embedding fails
            vec = []
            
        # Tool-call like filtering via request filters
        sections = None
        if req.filters and req.filters.get("sections"):
            sections = [str(s).lower() for s in req.filters.get("sections")]
        per_resume = int(settings.RETRIEVAL_PER_RESUME_LIMIT)
        
        vector_available = detect_vector_support()
        log.info("chat_start", vector_support=vector_available, query_preview=query[:100])
        
        try:
            results = hybrid_search_adv(session, query, vec, top_k=20, per_resume_limit=per_resume, sections=sections)
            context, citations = build_context_from_chunks(results)
        except Exception as e:
            log.error("chat_retrieval_failed", error=str(e), query=query[:100])
            # Fallback to minimal context if retrieval fails
            context = f"Unable to retrieve context due to error: {str(e)}"
            citations = []

    def event_stream():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agen = rag_chat_stream(query, context, citations)
        try:
            # First send meta with citations
            meta = loop.run_until_complete(agen.__anext__())
            yield f"event: meta\ndata: {json.dumps(meta)}\n\n"

            # Chat-time tool-calls (prelude) based on filters
            # 1) Fetch facts for specific resume_id(s)
            try:
                if req.filters and req.filters.get("resume_ids"):
                    with SessionLocal() as session2:
                        facts_payload = []
                        for rid in req.filters.get("resume_ids"):
                            f = session2.get(models.ResumeFacts, rid)
                            if f:
                                facts_payload.append({"resume_id": rid, "facts": f.extracted_json, "scores": f.scores})
                        if facts_payload:
                            yield _emit_tool_event("fetch_facts", {"results": facts_payload})
            except Exception:
                pass

            # 2) Recompute match for a provided JD
            try:
                if req.filters and req.filters.get("job_description"):
                    jd = str(req.filters.get("job_description"))
                    with SessionLocal() as session3:
                        vec_jd = loop.run_until_complete(embed_text(jd))
                        matches = hybrid_search_adv(session3, jd, vec_jd, top_k=20, per_resume_limit=per_resume)
                        grouped: dict[str, float] = {}
                        for ch, score in matches:
                            rid = str(ch.resume_id)
                            grouped[rid] = grouped.get(rid, 0.0) + (1.0 / (1.0 + score))
                        top = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:20]
                        yield _emit_tool_event("match_job", {"matches": [{"resume_id": rid, "score": s} for rid, s in top]})
            except Exception:
                pass

            # 3) Filter by attributes (seniority/domain)
            try:
                if req.filters and (req.filters.get("seniority") or req.filters.get("domain")):
                    with SessionLocal() as session4:
                        q = session4.query(models.ResumeFacts)
                        if req.filters.get("seniority"):
                            sen = str(req.filters.get("seniority")).lower()
                            q = q.filter(text("(extracted_json->>'seniority') ILIKE :sen"))
                            q = q.params(sen=f"%{sen}%")
                        if req.filters.get("domain"):
                            dom = str(req.filters.get("domain")).lower()
                            q = q.filter(text(":dom = ANY(SELECT jsonb_array_elements_text(extracted_json->'domain'))")).params(dom=dom)
                        rows = q.limit(50).all()
                        yield _emit_tool_event("filter_attributes", {"count": len(rows), "resume_ids": [str(r.resume_id) for r in rows]})
            except Exception:
                pass

            # Now stream model deltas
            while True:
                try:
                    ev = loop.run_until_complete(agen.__anext__())
                except StopAsyncIteration:
                    break
                if ev.get("type") == "delta":
                    yield f"data: {json.dumps(ev)}\n\n"
                else:
                    yield f"event: {ev.get('type','message')}\ndata: {json.dumps(ev)}\n\n"
        finally:
            try:
                loop.run_until_complete(agen.aclose())
            except Exception:
                pass
            loop.close()

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    log.info("chat_start", session_id=req.session_id, citations=len(citations))
    return Response(event_stream(), mimetype="text/event-stream", headers=headers)


# Status Monitoring Endpoints

@bp.route("/status/overview", methods=["GET"])
def status_overview():
    """Get system-wide resume analysis overview"""
    from app.services.status_monitor import get_system_overview
    try:
        stats = get_system_overview()
        return jsonify(stats)
    except Exception as e:
        log.error("status_overview_failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/status/resumes", methods=["GET"])
def status_all_resumes():
    """Get status for all resumes with pagination"""
    from app.services.status_monitor import StatusMonitor
    
    try:
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))
        
        with StatusMonitor() as monitor:
            statuses = monitor.get_all_resume_statuses(limit=limit, offset=offset)
            
        return jsonify({
            "resumes": [status.to_dict() for status in statuses],
            "limit": limit,
            "offset": offset,
            "count": len(statuses)
        })
    except Exception as e:
        log.error("status_all_resumes_failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/status/resumes/<resume_id>", methods=["GET"])
def status_single_resume(resume_id: str):
    """Get detailed status for a specific resume"""
    from app.services.status_monitor import check_resume_status
    
    try:
        status = check_resume_status(resume_id)
        if not status:
            return jsonify({"error": "Resume not found"}), 404
        
        return jsonify(status)
    except Exception as e:
        log.error("status_single_resume_failed", resume_id=resume_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/status/stuck", methods=["GET"])
def status_stuck_resumes():
    """Find resumes that are stuck in processing"""
    from app.services.status_monitor import StatusMonitor
    
    try:
        minutes_threshold = int(request.args.get("minutes", 10))
        
        with StatusMonitor() as monitor:
            stuck_resumes = monitor.find_stuck_resumes(minutes_threshold)
            
        return jsonify({
            "stuck_resumes": [status.to_dict() for status in stuck_resumes],
            "count": len(stuck_resumes),
            "minutes_threshold": minutes_threshold
        })
    except Exception as e:
        log.error("status_stuck_resumes_failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/status/ready", methods=["GET"])
def status_ready_resumes():
    """Find resumes ready for analysis (have text but no facts)"""
    from app.services.status_monitor import StatusMonitor
    
    try:
        with StatusMonitor() as monitor:
            ready_resumes = monitor.find_ready_for_analysis()
            
        return jsonify({
            "ready_resumes": [status.to_dict() for status in ready_resumes],
            "count": len(ready_resumes)
        })
    except Exception as e:
        log.error("status_ready_resumes_failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/actions/trigger/<resume_id>", methods=["POST"])
def trigger_resume_analysis(resume_id: str):
    """Trigger analysis for a specific resume"""
    from app.services.status_monitor import trigger_resume_analysis as trigger_analysis
    
    try:
        force = request.json.get("force", False) if request.json else False
        
        success = trigger_analysis(resume_id, force=force)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Analysis triggered for resume {resume_id}",
                "resume_id": resume_id,
                "force": force
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Failed to trigger analysis for resume {resume_id}",
                "resume_id": resume_id
            }), 400
            
    except Exception as e:
        log.error("trigger_resume_analysis_failed", resume_id=resume_id, error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/actions/auto-recover", methods=["POST"])
def auto_recover_stuck():
    """Automatically recover stuck resumes and trigger ready ones"""
    from app.services.status_monitor import auto_recover_system
    
    try:
        dry_run = request.json.get("dry_run", False) if request.json else False
        
        results = auto_recover_system()
        
        if dry_run:
            results["dry_run"] = True
            
        return jsonify({
            "success": True,
            "results": results,
            "message": f"Auto-recovery completed. Recovered: {results.get('recovered', 0)}, Triggered: {results.get('triggered', 0)}"
        })
        
    except Exception as e:
        log.error("auto_recover_stuck_failed", error=str(e))
        return jsonify({"error": str(e)}), 500


@bp.route("/actions/trigger-all-ready", methods=["POST"])
def trigger_all_ready():
    """Trigger analysis for all ready resumes"""
    from app.services.status_monitor import StatusMonitor
    
    try:
        with StatusMonitor() as monitor:
            ready_resumes = monitor.find_ready_for_analysis()
            
            triggered = 0
            errors = []
            
            for status in ready_resumes:
                try:
                    if monitor.trigger_analysis(status.id):
                        triggered += 1
                        log.info("trigger_ready_resume", resume_id=status.id)
                    else:
                        errors.append(f"Failed to trigger {status.id}")
                except Exception as e:
                    errors.append(f"Error triggering {status.id}: {str(e)}")
            
            return jsonify({
                "success": True,
                "triggered": triggered,
                "total_ready": len(ready_resumes),
                "errors": errors,
                "message": f"Triggered analysis for {triggered}/{len(ready_resumes)} ready resumes"
            })
            
    except Exception as e:
        log.error("trigger_all_ready_failed", error=str(e))
        return jsonify({"error": str(e)}), 500
