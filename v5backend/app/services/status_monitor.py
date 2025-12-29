"""
Resume Analysis Status Monitor

Provides functionality to check resume analysis status and automatically trigger
processing for stuck or unprocessed resumes.
"""
from __future__ import annotations
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, text
from app.db.session import SessionLocal
from app.db import models
from app.workers.celery_app import celery_app
from app.core.logging import get_logger
from app.core.config import settings

log = get_logger("status_monitor")


def _try_to_find_s3_key_for_resume(resume: models.Resume, session: Session) -> str | None:
    """
    Try to find the actual S3 key for a resume that doesn't have s3_key set.
    This is for backwards compatibility with existing resumes.
    """
    if resume.s3_key:
        return resume.s3_key
        
    # Try to find the key by looking for common patterns
    from app.services.storage import get_s3_client
    try:
        s3 = get_s3_client()
        
        # Try different key patterns that might have been used
        possible_keys = [
            f"resume_{resume.id}",  # Old fabricated format (incorrect)
            str(resume.id),         # Just the UUID
            f"{resume.id}.pdf",     # UUID with extension
            f"{resume.id}.docx",    # UUID with extension
        ]
        
        for key in possible_keys:
            try:
                s3.head_object(Bucket=settings.S3_BUCKET, Key=key)
                # Found it! Update the database
                resume.s3_key = key
                session.commit()
                log.info("found_missing_s3_key", resume_id=str(resume.id), s3_key=key)
                return key
            except Exception:
                continue
        
        log.warning("s3_key_not_found", resume_id=str(resume.id))
        return None
        
    except Exception as e:
        log.error("s3_key_search_failed", resume_id=str(resume.id), error=str(e))
        return None


class ResumeStatus:
    """Resume analysis status information"""
    def __init__(self, resume: models.Resume, facts: Optional[models.ResumeFacts] = None, 
                 text: Optional[models.ResumeText] = None, chunks_count: int = 0):
        self.resume = resume
        self.facts = facts
        self.text = text
        self.chunks_count = chunks_count
    
    @property
    def id(self) -> str:
        return str(self.resume.id)
    
    @property
    def status(self) -> str:
        return self.resume.status
    
    @property
    def current_pass(self) -> int:
        try:
            if self.facts and self.facts.scores:
                p = int(self.facts.scores.get("pass") or 0)
                if p:
                    return p
        except Exception:
            pass
        # Derive from status if not in scores
        if self.status == "complete":
            return 3
        if self.status == "complete_p2":
            return 2
        if self.status == "complete_p1":
            return 1
        return 0
    
    @property
    def is_complete(self) -> bool:
        return self.status == "complete" and self.facts is not None
    
    @property
    def is_stuck(self) -> bool:
        """Check if resume is stuck in processing for too long"""
        if self.status in ["complete", "duplicate", "failed"]:
            return False
        
        # Consider stuck if processing for more than 10 minutes
        time_threshold = datetime.utcnow() - timedelta(minutes=10)
        return self.resume.updated_at < time_threshold
    
    @property
    def is_ready_for_analysis(self) -> bool:
        """Check if resume has text extracted but no facts"""
        return (self.text is not None and 
                self.facts is None and 
                self.status not in ["duplicate", "failed", "complete", "complete_p1", "complete_p2"])
    
    @property
    def analysis_stage(self) -> str:
        """Determine what stage of analysis the resume is in"""
        if self.status == "complete" and self.facts:
            confidence = self.facts.scores.get("confidence", 0.0) if self.facts.scores else 0.0
            return f"complete (pass: 3, confidence: {confidence:.2f})"
        elif self.status == "complete_p2" and self.facts:
            confidence = self.facts.scores.get("confidence", 0.0) if self.facts.scores else 0.0
            return f"pass2_complete (confidence: {confidence:.2f})"
        elif self.status == "complete_p1" and self.facts:
            confidence = self.facts.scores.get("confidence", 0.0) if self.facts.scores else 0.0
            return f"pass1_complete (confidence: {confidence:.2f})"
        elif self.status == "duplicate":
            return "duplicate"
        elif self.status == "failed":
            return "failed"
        elif self.facts:
            # Facts exist but status isn't marked complete - treat as analyzed
            return f"analyzed (facts extracted, pass: {self.current_pass or 'n/a'})"
        elif self.chunks_count > 0:
            return "chunked (embeddings generated)"
        elif self.text:
            return "text_extracted"
        elif self.status == "processing":
            return "processing (extracting text)"
        elif self.status == "queued":
            return "queued"
        else:
            return f"unknown ({self.status})"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "filename": self.resume.original_filename,
            "status": self.status,
            "analysis_stage": self.analysis_stage,
            "current_pass": self.current_pass,
            "is_complete": self.is_complete,
            "is_stuck": self.is_stuck,
            "is_ready_for_analysis": self.is_ready_for_analysis,
            "created_at": self.resume.created_at.isoformat(),
            "updated_at": self.resume.updated_at.isoformat(),
            "size": self.resume.size,
            "mime": self.resume.mime,
            "s3_key": self.resume.s3_key,
            "error_message": self.resume.error_message,
            "has_text": self.text is not None,
            "has_chunks": self.chunks_count > 0,
            "has_facts": self.facts is not None,
            "confidence": self.facts.scores.get("confidence", 0.0) if self.facts and self.facts.scores else None,
        }


class StatusMonitor:
    """Resume analysis status monitoring and recovery"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
        self._own_session = session is None
    
    def __enter__(self):
        if self._own_session:
            self.session = SessionLocal()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._own_session and self.session:
            self.session.close()
    
    def get_resume_status(self, resume_id: str) -> Optional[ResumeStatus]:
        """Get detailed status for a specific resume"""
        try:
            # Get resume with related data
            resume = self.session.get(models.Resume, resume_id)
            if not resume:
                return None
            
            facts = self.session.get(models.ResumeFacts, resume_id)
            text = self.session.get(models.ResumeText, resume_id)
            
            # Count chunks
            chunks_count = self.session.scalar(
                select(func.count(models.ResumeChunk.id))
                .where(models.ResumeChunk.resume_id == resume_id)
            ) or 0
            
            return ResumeStatus(resume, facts, text, chunks_count)
        except Exception as e:
            log.error("get_resume_status_failed", resume_id=resume_id, error=str(e))
            return None
    
    def get_all_resume_statuses(self, limit: int = 100, offset: int = 0) -> List[ResumeStatus]:
        """Get status for all resumes with pagination"""
        try:
            # Get resumes ordered by creation date (newest first)
            resumes = self.session.execute(
                select(models.Resume)
                .order_by(models.Resume.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).scalars().all()
            
            statuses = []
            for resume in resumes:
                facts = self.session.get(models.ResumeFacts, resume.id)
                text = self.session.get(models.ResumeText, resume.id)
                chunks_count = self.session.scalar(
                    select(func.count(models.ResumeChunk.id))
                    .where(models.ResumeChunk.resume_id == resume.id)
                ) or 0
                
                statuses.append(ResumeStatus(resume, facts, text, chunks_count))
            
            return statuses
        except Exception as e:
            log.error("get_all_resume_statuses_failed", error=str(e))
            return []
    
    def find_stuck_resumes(self, minutes_threshold: int = 10) -> List[ResumeStatus]:
        """Find resumes that are stuck in processing"""
        try:
            time_threshold = datetime.utcnow() - timedelta(minutes=minutes_threshold)
            
            stuck_resumes = self.session.execute(
                select(models.Resume)
                .where(
                    and_(
                        models.Resume.status.in_(["queued", "processing"]),
                        models.Resume.updated_at < time_threshold
                    )
                )
                .order_by(models.Resume.updated_at.asc())
            ).scalars().all()
            
            statuses = []
            for resume in stuck_resumes:
                facts = self.session.get(models.ResumeFacts, resume.id)
                text = self.session.get(models.ResumeText, resume.id)
                chunks_count = self.session.scalar(
                    select(func.count(models.ResumeChunk.id))
                    .where(models.ResumeChunk.resume_id == resume.id)
                ) or 0
                
                status = ResumeStatus(resume, facts, text, chunks_count)
                if status.is_stuck:
                    statuses.append(status)
            
            return statuses
        except Exception as e:
            log.error("find_stuck_resumes_failed", error=str(e))
            return []
    
    def find_ready_for_analysis(self) -> List[ResumeStatus]:
        """Find resumes that have text but no analysis (facts)"""
        try:
            # Get resumes that have text but no facts
            resumes_with_text_no_facts = self.session.execute(
                select(models.Resume)
                .join(models.ResumeText, models.Resume.id == models.ResumeText.resume_id)
                .outerjoin(models.ResumeFacts, models.Resume.id == models.ResumeFacts.resume_id)
                .where(
                    and_(
                        models.ResumeFacts.resume_id.is_(None),  # No facts
                        models.Resume.status.notin_(["duplicate", "failed", "complete", "complete_p1", "complete_p2"])
                    )
                )
                .order_by(models.Resume.created_at.asc())
            ).scalars().all()
            
            statuses = []
            for resume in resumes_with_text_no_facts:
                text = self.session.get(models.ResumeText, resume.id)
                chunks_count = self.session.scalar(
                    select(func.count(models.ResumeChunk.id))
                    .where(models.ResumeChunk.resume_id == resume.id)
                ) or 0
                
                status = ResumeStatus(resume, None, text, chunks_count)
                if status.is_ready_for_analysis:
                    statuses.append(status)
            
            return statuses
        except Exception as e:
            log.error("find_ready_for_analysis_failed", error=str(e))
            return []
    
    def trigger_analysis(self, resume_id: str, force: bool = False) -> bool:
        """Trigger analysis for a specific resume"""
        try:
            status = self.get_resume_status(resume_id)
            if not status:
                log.warning("trigger_analysis_resume_not_found", resume_id=resume_id)
                return False
            
            # Determine what stage to trigger
            if status.is_complete and not force:
                log.info("trigger_analysis_already_complete", resume_id=resume_id)
                return True
            
            if status.text is None:
                # Need to start from the beginning (IO stage)
                log.info("trigger_analysis_from_io", resume_id=resume_id)
                
                # Check if we have the S3 key stored, or try to find it
                s3_key = status.resume.s3_key or _try_to_find_s3_key_for_resume(status.resume, self.session)
                
                if not s3_key:
                    log.error("trigger_analysis_missing_s3_key", resume_id=resume_id)
                    status.resume.status = "failed"
                    status.resume.error_message = "S3 key not found - file may have been deleted or uploaded incorrectly"
                    self.session.commit()
                    return False
                
                # Update status to queued
                status.resume.status = "queued"
                status.resume.error_message = None  # Clear any previous error
                status.resume.updated_at = datetime.utcnow()
                self.session.commit()
                
                # Queue IO processing with the actual S3 key
                celery_app.signature(
                    "process_resume_io", 
                    args=[resume_id, s3_key, status.resume.original_filename, status.resume.size]
                ).apply_async(queue="io")
                
            elif status.chunks_count == 0:
                # Has text but no chunks - need embedding stage
                log.info("trigger_analysis_from_embedding", resume_id=resume_id)
                
                # Get text and create chunks
                from app.services.chunker import section_aware_chunks
                text_content = status.text.full_text
                sec_chunks = section_aware_chunks(text_content)
                chunks = [c["text"] for c in sec_chunks]
                sections = [str(c.get("section") or "unknown") for c in sec_chunks]
                
                # Queue embedding stage
                celery_app.signature(
                    "embed_chunks_io", 
                    args=[resume_id, chunks, sections]
                ).apply_async(queue="io")
                
            elif status.facts is None:
                # Has chunks but no analysis - need LLM stage
                log.info("trigger_analysis_from_llm", resume_id=resume_id)
                
                # Queue LLM analysis (multi-pass entry)
                celery_app.signature(
                    "analyze_resume_llm", 
                    args=[resume_id]
                ).apply_async(queue="llm")
            
            else:
                # Force reanalysis => kick off pass1 again
                if force:
                    log.info("trigger_analysis_force_rerun", resume_id=resume_id)
                    
                    # Delete existing facts to trigger reanalysis
                    if status.facts:
                        self.session.delete(status.facts)
                        self.session.commit()
                    
                    # Queue LLM analysis
                    celery_app.signature(
                        "analyze_resume_llm", 
                        args=[resume_id]
                    ).apply_async(queue="llm")
                else:
                    log.info("trigger_analysis_no_action_needed", resume_id=resume_id)
            
            return True
            
        except Exception as e:
            log.error("trigger_analysis_failed", resume_id=resume_id, error=str(e))
            self.session.rollback()
            return False
    
    def auto_recover_stuck_resumes(self, dry_run: bool = False) -> Dict:
        """Automatically recover stuck resumes"""
        try:
            stuck_resumes = self.find_stuck_resumes()
            ready_resumes = self.find_ready_for_analysis()
            
            results = {
                "stuck_found": len(stuck_resumes),
                "ready_found": len(ready_resumes),
                "recovered": 0,
                "triggered": 0,
                "errors": []
            }
            
            if dry_run:
                results["dry_run"] = True
                return results
            
            # Recover stuck resumes
            for status in stuck_resumes:
                try:
                    if self.trigger_analysis(status.id):
                        results["recovered"] += 1
                        log.info("auto_recover_stuck", resume_id=status.id, stage=status.analysis_stage)
                    else:
                        results["errors"].append(f"Failed to recover {status.id}")
                except Exception as e:
                    results["errors"].append(f"Error recovering {status.id}: {str(e)}")
            
            # Trigger analysis for ready resumes
            for status in ready_resumes:
                try:
                    if self.trigger_analysis(status.id):
                        results["triggered"] += 1
                        log.info("auto_trigger_ready", resume_id=status.id)
                    else:
                        results["errors"].append(f"Failed to trigger {status.id}")
                except Exception as e:
                    results["errors"].append(f"Error triggering {status.id}: {str(e)}")
            
            log.info("auto_recovery_complete", **{k: v for k, v in results.items() if k != "errors"})
            return results
            
        except Exception as e:
            log.error("auto_recover_failed", error=str(e))
            return {"error": str(e)}
    
    def get_system_stats(self) -> Dict:
        """Get system-wide resume analysis statistics"""
        try:
            total_resumes = self.session.scalar(select(func.count(models.Resume.id))) or 0
            
            # Count by status
            status_counts = {}
            status_results = self.session.execute(
                select(models.Resume.status, func.count(models.Resume.id))
                .group_by(models.Resume.status)
            ).all()
            
            for status, count in status_results:
                status_counts[status] = count
            
            # Count completed analyses
            completed_analyses = self.session.scalar(
                select(func.count(models.ResumeFacts.resume_id))
            ) or 0
            
            # Count with text extracted
            with_text = self.session.scalar(
                select(func.count(models.ResumeText.resume_id))
            ) or 0
            
            # Count with chunks
            with_chunks = self.session.scalar(
                select(func.count(func.distinct(models.ResumeChunk.resume_id)))
            ) or 0
            
            # Average confidence for completed analyses
            avg_confidence = self.session.scalar(
                select(func.avg(func.cast(func.json_extract_path_text(models.ResumeFacts.scores, 'confidence'), float)))
                .where(func.json_extract_path_text(models.ResumeFacts.scores, 'confidence').isnot(None))
            ) or 0.0
            
            return {
                "total_resumes": total_resumes,
                "status_counts": status_counts,
                "analysis_stats": {
                    "completed_analyses": completed_analyses,
                    "with_text": with_text,
                    "with_chunks": with_chunks,
                    "avg_confidence": round(float(avg_confidence), 3) if avg_confidence else 0.0,
                    "completion_rate": round((completed_analyses / total_resumes * 100), 2) if total_resumes > 0 else 0.0
                },
                "stuck_count": len(self.find_stuck_resumes()),
                "ready_for_analysis": len(self.find_ready_for_analysis())
            }
            
        except Exception as e:
            log.error("get_system_stats_failed", error=str(e))
            return {"error": str(e)}


def check_resume_status(resume_id: str) -> Optional[Dict]:
    """Quick status check for a single resume"""
    with StatusMonitor() as monitor:
        status = monitor.get_resume_status(resume_id)
        return status.to_dict() if status else None


def trigger_resume_analysis(resume_id: str, force: bool = False) -> bool:
    """Trigger analysis for a specific resume"""
    with StatusMonitor() as monitor:
        return monitor.trigger_analysis(resume_id, force)


def auto_recover_system() -> Dict:
    """Auto-recover stuck resumes system-wide"""
    with StatusMonitor() as monitor:
        return monitor.auto_recover_stuck_resumes()


def get_system_overview() -> Dict:
    """Get system-wide analysis overview"""
    with StatusMonitor() as monitor:
        return monitor.get_system_stats()
