from __future__ import annotations
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from app.db.models import ResumeChunk, ResumeText, Resume
from app.core.config import settings
from app.services.vector_support import detect_vector_support, vector_fallback
import math
from typing import Iterable


def ensure_fulltext(session: Session):
    session.execute(text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'resume_text_fts') THEN
                ALTER TABLE resume_text ADD COLUMN IF NOT EXISTS fts tsvector;
                UPDATE resume_text SET fts = to_tsvector('english', full_text);
                CREATE INDEX resume_text_fts ON resume_text USING GIN (fts);
            END IF;
        END
        $$;
    """))
    session.commit()


def search_fulltext(session: Session, query: str, top_k: int = 20):
    ensure_fulltext(session)
    q = text("""
        SELECT resume_id
        FROM resume_text
        WHERE fts @@ plainto_tsquery('english', :q)
        LIMIT :k
    """)
    rows = session.execute(q, {"q": query, "k": top_k}).fetchall()
    return [str(r[0]) for r in rows]


def search_similar(session: Session, query_vec: list[float], resume_ids: list[str] | None = None, top_k: int = 20, offset: int = 0):
    """Search using vector similarity. Requires vector support."""
    if not detect_vector_support():
        raise RuntimeError("Vector search not available - use text-only search instead")
    
    stmt = select(ResumeChunk, ResumeChunk.embedding.l2_distance(query_vec).label("score")).order_by("score").limit(top_k).offset(offset)
    if resume_ids:
        stmt = stmt.where(ResumeChunk.resume_id.in_(resume_ids))
    rows = session.execute(stmt).all()
    return [(row[0], float(row[1])) for row in rows]


def search_similar_fallback(session: Session, query_vec: list[float], resume_ids: list[str] | None = None, top_k: int = 20, offset: int = 0):
    """Fallback search using text-based ranking when vector search is unavailable."""
    # Simple fallback: return recent chunks with basic text scoring
    stmt = select(ResumeChunk).order_by(ResumeChunk.id.desc()).limit(top_k).offset(offset)
    if resume_ids:
        stmt = stmt.where(ResumeChunk.resume_id.in_(resume_ids))
    
    rows = session.execute(stmt).all()
    # Assign dummy scores based on recency and section weights
    results = []
    for i, chunk in enumerate(rows):
        section_weight = SECTION_WEIGHTS.get(getattr(chunk, "section", "unknown"), 0.8)
        # Higher score for more recent chunks, adjusted by section weight
        score = (1.0 + i * 0.1) * section_weight
        results.append((chunk, score))
    
    return results


# Apply fallback decorator
search_similar = vector_fallback(search_similar_fallback)(search_similar)


def search_similar_filtered(session: Session, query_vec: list[float], resume_ids: list[str] | None = None, sections: list[str] | None = None, limit: int = 100):
    """Search using vector similarity with filtering. Requires vector support."""
    if not detect_vector_support():
        raise RuntimeError("Vector search not available - use text-only search instead")
    
    stmt = select(ResumeChunk, ResumeChunk.embedding.l2_distance(query_vec).label("score")).order_by("score").limit(limit)
    if resume_ids:
        stmt = stmt.where(ResumeChunk.resume_id.in_(resume_ids))
    if sections:
        stmt = stmt.where(ResumeChunk.section.in_(sections))
    rows = session.execute(stmt).all()
    return [(row[0], float(row[1])) for row in rows]


def search_similar_filtered_fallback(session: Session, query_vec: list[float], resume_ids: list[str] | None = None, sections: list[str] | None = None, limit: int = 100):
    """Fallback search with filtering when vector search is unavailable."""
    stmt = select(ResumeChunk).order_by(ResumeChunk.id.desc()).limit(limit)
    if resume_ids:
        stmt = stmt.where(ResumeChunk.resume_id.in_(resume_ids))
    if sections:
        stmt = stmt.where(ResumeChunk.section.in_(sections))
    
    rows = session.execute(stmt).all()
    results = []
    for i, chunk in enumerate(rows):
        section_weight = SECTION_WEIGHTS.get(getattr(chunk, "section", "unknown"), 0.8)
        score = (1.0 + i * 0.1) * section_weight
        results.append((chunk, score))
    
    return results


# Apply fallback decorator
search_similar_filtered = vector_fallback(search_similar_filtered_fallback)(search_similar_filtered)


def hybrid_search(session: Session, query: str, query_vec: list[float], top_k: int = 20, page: int = 1, page_size: int = 20):
    """Hybrid search combining full-text and vector search with fallback support."""
    ft_ids = set(search_fulltext(session, query, top_k * 5))
    offset = (page - 1) * page_size
    
    if detect_vector_support():
        results = search_similar(session, query_vec, list(ft_ids) if ft_ids else None, top_k=page_size, offset=offset)
    else:
        # Fallback to text-only search with filtering
        results = search_similar_fallback(session, query_vec, list(ft_ids) if ft_ids else None, top_k=page_size, offset=offset)
    
    return results


SECTION_WEIGHTS = {
    "experience": 1.0,
    "projects": 0.95,
    "skills": 0.9,
    "education": 0.85,
    "summary": 0.8,
    "certifications": 0.85,
    "unknown": 0.8,
}


def _cos_sim(a: Iterable[float], b: Iterable[float]) -> float:
    ax = list(a)
    bx = list(b)
    num = sum(x * y for x, y in zip(ax, bx))
    da = math.sqrt(sum(x * x for x in ax)) or 1e-8
    db = math.sqrt(sum(y * y for y in bx)) or 1e-8
    return num / (da * db)


def hybrid_search_adv(
    session: Session,
    query: str,
    query_vec: list[float],
    *,
    top_k: int = 20,
    per_resume_limit: int = 3,
    sections: list[str] | None = None,
    rrf_k: int = 60,
    w_vec: float = 0.7,
    w_ft: float = 0.3,
    mmr_lambda: float = 0.5,
    candidate_multiplier: int = 10,
):
    """Advanced hybrid search with RRF scoring and MMR selection, with vector fallback support."""
    # FT ranks at resume level
    ft_ids = search_fulltext(session, query, top_k * 10)
    ft_rank = {rid: i for i, rid in enumerate(ft_ids)}

    # Candidate pool filtered by section/resume ids (from FT list if present)
    resume_filter = ft_ids if ft_ids else None
    
    if detect_vector_support():
        candidates = search_similar_filtered(session, query_vec, resume_ids=resume_filter, sections=sections, limit=top_k * candidate_multiplier)
    else:
        # Fallback to text-only search when vector support unavailable
        from sqlalchemy import func
        q = session.query(ResumeChunk).filter(ResumeChunk.text.isnot(None))
        
        if resume_filter:
            q = q.filter(ResumeChunk.resume_id.in_(resume_filter))
        if sections:
            q = q.filter(ResumeChunk.section.in_(sections))
            
        # Use text search ranking as substitute for vector similarity
        candidates = [(chunk, 0.5) for chunk in q.limit(top_k * candidate_multiplier).all()]

    # RRF scoring combining vector order and FT resume rank
    rrf_candidates = []
    for rank_vec, (ch, dist) in enumerate(candidates, start=1):
        vec_rank_contrib = 1.0 / (rrf_k + rank_vec)
        ft_contrib = 0.0
        rrank = ft_rank.get(str(ch.resume_id))
        if rrank is not None:
            ft_contrib = 1.0 / (rrf_k + (rrank + 1))
        rrf_score = w_vec * vec_rank_contrib + w_ft * ft_contrib
        vec_rel = 1.0 / (1.0 + dist)
        sec_w = SECTION_WEIGHTS.get(getattr(ch, "section", "unknown"), SECTION_WEIGHTS["unknown"])
        base_rel = (0.7 * vec_rel + 0.3 * ft_contrib) * sec_w
        rrf_candidates.append({
            "chunk": ch,
            "dist": dist,
            "vec_rel": vec_rel,
            "ft_contrib": ft_contrib,
            "rrf": rrf_score,
            "rel": base_rel,
        })

    # MMR selection
    selected: list[tuple[ResumeChunk, float]] = []
    selected_vecs: list[list[float]] = []
    per_resume: dict[str, int] = {}

    while rrf_candidates and len(selected) < top_k:
        best = None
        best_score = -1e9
        best_idx = -1
        for i, item in enumerate(rrf_candidates):
            ch: ResumeChunk = item["chunk"]
            rid = str(ch.resume_id)
            if per_resume.get(rid, 0) >= per_resume_limit:
                continue
            rel = item["rel"]
            # diversity penalty - skip if no vector support
            if selected_vecs and detect_vector_support() and hasattr(ch, 'embedding') and ch.embedding:
                sim = max(_cos_sim(ch.embedding, v) for v in selected_vecs)
            else:
                sim = 0.0
            mmr = mmr_lambda * rel - (1.0 - mmr_lambda) * sim
            if mmr > best_score:
                best_score = mmr
                best = ch
                best_idx = i
        if best is None:
            break
        selected.append((best, float(best_score)))
        # Only track vectors if vector support available
        if detect_vector_support() and hasattr(best, 'embedding') and best.embedding:
            selected_vecs.append(list(best.embedding))
        rid = str(best.resume_id)
        per_resume[rid] = per_resume.get(rid, 0) + 1
        # remove selected
        rrf_candidates.pop(best_idx)

    return selected


def build_context_from_chunks(chunks_with_scores: list[tuple[ResumeChunk, float]], max_chars: int = 6000) -> tuple[str, list[dict]]:
    buf = []
    cites = []
    total = 0
    for ch, score in chunks_with_scores:
        t = ch.text[:1000]
        if total + len(t) > max_chars:
            break
        citation = {"resume_id": str(ch.resume_id), "chunk_idx": ch.idx, "score": score, "section": getattr(ch, "section", "unknown")}
        section = citation["section"]
        buf.append(f"[Resume {citation['resume_id']} chunk {citation['chunk_idx']} score {score:.4f} section {section}]\n{t}")
        cites.append(citation)
        total += len(t)
    return "\n\n".join(buf), cites
