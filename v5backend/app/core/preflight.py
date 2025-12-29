from __future__ import annotations
import os
import time
from typing import Optional

from sqlalchemy import text, create_engine
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db import session as db_session
from app.services.storage import ensure_buckets_existence, get_s3_client

try:
    import redis as _redis
except Exception:  # pragma: no cover
    _redis = None  # type: ignore

try:
    from alembic.config import Config
    from alembic import command
    ALEMBIC_AVAILABLE = True
except ImportError:  # pragma: no cover
    ALEMBIC_AVAILABLE = False

# Track schema readiness for summary output
_LAST_DB_SCHEMA_OK: Optional[bool] = None
# Keep richer details for printing a helpful summary line
_LAST_DB_SCHEMA_DETAILS: Optional[dict] = None


def _retry_until_ok(fn, *, name: str, timeout: int = 90, interval: float = 3.0) -> bool:
    log = get_logger("preflight")
    deadline = time.time() + timeout
    attempt = 0
    while True:
        attempt += 1
        try:
            fn()
            log.info("check_ok", target=name, attempt=attempt)
            return True
        except Exception as e:  # pragma: no cover
            if time.time() >= deadline:
                log.error("check_timeout", target=name, attempt=attempt, error=str(e))
                return False
            log.warning("check_retry", target=name, attempt=attempt, error=str(e))
            time.sleep(interval)


def _candidate_db_urls() -> list[str]:
    urls: list[str] = []
    
    # Get common connection details
    pguser = os.getenv("PGUSER") or os.getenv("POSTGRES_USER") or "postgres"
    pgpassword = os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD") or ""
    pgdb = os.getenv("PGDATABASE") or os.getenv("POSTGRES_DB") or "railway"  # Default to 'railway' for Railway platform
    
    # Common connection parameters to fix session context issues
    conn_params = "?application_name=preflight_check&connect_timeout=30&sslmode=prefer"
    
    # Priority 1: DATABASE_INTERNAL_URL (pgpool - most reliable inside Railway)
    env_internal = os.getenv("DATABASE_INTERNAL_URL")
    if env_internal:
        urls.append(env_internal)
    
    # Priority 2: Build from PGHOST/PGPORT if pointing to internal service
    pghost = os.getenv("PGHOST") or os.getenv("POSTGRES_HOST")
    pgport = os.getenv("PGPORT") or os.getenv("POSTGRES_PORT")
    if pghost and pgport and pgpassword:
        # If PGHOST is internal Railway service, prefer it
        if "railway.internal" in pghost or pghost == "pgpool.railway.internal":
            url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdb}{conn_params}"
            urls.append(url)
    
    # Priority 3: HA Cluster individual nodes (direct internal connections)
    # Try primary node first
    primary_url = os.getenv("DATABASE_PRIMARY_NODE")
    if primary_url:
        urls.append(primary_url)
    
    # Then try replica nodes
    replica_1 = os.getenv("DATABASE_REPLICA_1")
    if replica_1:
        urls.append(replica_1)
    
    replica_2 = os.getenv("DATABASE_REPLICA_2")
    if replica_2:
        urls.append(replica_2)
    
    # Priority 4: DATABASE_URL from settings (may be TCP proxy)
    if settings.DATABASE_URL:
        # Add parameters if not already present
        db_url = settings.DATABASE_URL
        if "?" not in db_url:
            db_url += conn_params
        urls.append(db_url)
    
    # Priority 5: DATABASE_PUBLIC_URL (TCP proxy - use as fallback)
    env_pub = os.getenv("DATABASE_PUBLIC_URL")
    if env_pub:
        urls.append(env_pub)
    
    # Priority 6: Build TCP proxy URL (last resort)
    if pghost and pgport and pgpassword and "railway.internal" not in pghost:
        url = f"postgresql://{pguser}:{pgpassword}@{pghost}:{pgport}/{pgdb}{conn_params}"
        urls.append(url)
    
    # Priority 7: Railway TCP proxy (explicit fallback)
    tcp_domain = os.getenv("RAILWAY_TCP_PROXY_DOMAIN") or os.getenv("RAILWAY_TCP_PROXY_HOST")
    tcp_port = os.getenv("RAILWAY_TCP_PROXY_PORT")
    if tcp_domain and tcp_port and pgpassword:
        url = f"postgresql://{pguser}:{pgpassword}@{tcp_domain}:{tcp_port}/{pgdb}{conn_params}"
        urls.append(url)

    # Normalize to psycopg driver and de-dup
    out: list[str] = []
    seen: set[str] = set()
    for u in urls:
        if u.startswith("postgresql://") and "+" not in u.split("://", 1)[0]:
            u = u.replace("postgresql://", "postgresql+psycopg://", 1)
        key = u.lower()
        if key not in seen:
            seen.add(key)
            out.append(u)
    return out


def _find_working_db_url() -> Optional[str]:
    log = get_logger("preflight.db")
    last_err: Optional[str] = None
    candidates = _candidate_db_urls()
    
    log.info("db_connection_attempt", candidates_count=len(candidates))
    
    for i, u in enumerate(candidates, 1):
        try:
            # Enhanced connection configuration for session context issues
            e = create_engine(
                u, 
                pool_pre_ping=True,
                pool_size=2,  # Smaller pool for preflight
                max_overflow=5,
                pool_timeout=30,
                pool_recycle=3600,
                connect_args={
                    "connect_timeout": 30,
                    "application_name": "preflight_check"
                }
            )
            with e.connect() as conn:
                # Test basic connectivity with explicit transaction
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row and row[0] == 1:
                    conn.commit()
                else:
                    raise Exception("Basic connectivity test failed")
            e.dispose()
            log.info("db_candidate_ok", candidate=i, url_type=u.split("@")[1].split("/")[0] if "@" in u else "unknown")
            return u
        except Exception as e:  # pragma: no cover
            last_err = str(e)
            log.warning("db_candidate_failed", candidate=i, error=last_err, url_type=u.split("@")[1].split("/")[0] if "@" in u else "unknown")
            # Ensure engine is disposed even on failure
            try:
                e.dispose()
            except:
                pass
    
    log.error("db_all_candidates_failed", error=last_err, total_candidates=len(candidates))
    return None


def check_postgres() -> bool:
    """Verify DB connectivity and ensure pgvector/tables exist. Log details.
    Returns True if connectivity is OK (schema status is logged separately)."""
    global _LAST_DB_SCHEMA_OK, _LAST_DB_SCHEMA_DETAILS
    log = get_logger("preflight.db")

    # Resolve a working DB URL (internal -> public proxy -> TCP proxy)
    working_url = _find_working_db_url()
    if not working_url:
        _LAST_DB_SCHEMA_OK = None
        _LAST_DB_SCHEMA_DETAILS = None
        log.error("postgres_unavailable", message="No working database URL found")
        return False

    # Inform caller (entrypoint) which URL is usable
    try:
        print(f"DB_SELECTED_URL={working_url}", flush=True)
    except Exception:
        pass

    # If different from current engine, swap it (effective only within this process)
    try:
        current_url = str(getattr(db_session.engine, "url", ""))
    except Exception:
        current_url = ""
    if current_url and working_url != current_url:
        log.info("db_engine_switch", from_url=current_url, to_url="<selected>")
        try:
            db_session.engine.dispose()
        except Exception:
            pass
        db_session.engine = create_engine(working_url, pool_pre_ping=True, pool_size=10, max_overflow=20)  # type: ignore[attr-defined]
        try:
            db_session.SessionLocal.configure(bind=db_session.engine)
        except Exception:
            pass

    # Enhanced connectivity + pgvector ensure with retry logic
    def _probe():
        with db_session.engine.connect() as conn:  # type: ignore[attr-defined]
            conn.execute(text("SELECT 1"))
            _attempt_pgvector_creation_preflight(conn, log)
            # After pgvector attempts (success or failure), ensure clean state
            try:
                conn.commit()  # Commit any successful operations
            except Exception:
                try:
                    conn.rollback()  # Rollback failed transactions
                except Exception:
                    pass

    ok = _retry_until_ok(_probe, name="postgres")
    
    # After preflight DB operations, dispose engine connections to ensure clean state for migrations
    try:
        db_session.engine.dispose()
        log.debug("db_engine_disposed", message="Disposed engine connections after preflight")
    except Exception as e:
        log.warning("db_engine_dispose_failed", error=str(e))
    
    if not ok:
        _LAST_DB_SCHEMA_OK = None
        _LAST_DB_SCHEMA_DETAILS = None
        log.error("postgres_unavailable", message="Database connectivity failed after retries")
        return False

    # Try to create tables if missing (only if Alembic is not available)
    try:
        import alembic
        # If Alembic is available, skip table creation - let migrations handle it
        log.info("alembic_detected", message="Skipping table creation - Alembic will handle migrations")
    except ImportError:
        # Alembic not available, create tables using SQLAlchemy
        try:
            # Import models to ensure metadata is loaded
            from app.db import models  # noqa: F401
            db_session.Base.metadata.create_all(bind=db_session.engine)  # type: ignore[attr-defined]
            log.info("tables_create_attempted")
        except Exception as e:
            log.warning("tables_create_failed", error=str(e))

    # Ensure FTS column + index for resume_text (defensive, migration may have already done this)
    try:
        from app.services.retriever import ensure_fulltext as _ensure_fts
        from app.db.session import SessionLocal as _SL
        with _SL() as _s:
            _ensure_fts(_s)
        log.info("fts_ensured", table="resume_text")
    except Exception as e:
        # This might fail if the table doesn't exist yet - migrations will handle it
        log.info("fts_ensure_skipped", error=str(e), message="Table may not exist yet - migrations will handle FTS setup")

    # Enhanced introspection for visibility with detailed logging
    _perform_db_introspection(log)
    
    # Treat connectivity as success even if schema is incomplete
    return True


def _attempt_pgvector_creation_preflight(conn, log):
    """Attempt to create pgvector extension during preflight with enhanced logging."""
    from app.core.config import settings
    
    if not settings.FORCE_PGVECTOR_CREATION:
        log.info("pgvector_creation_skipped", message="FORCE_PGVECTOR_CREATION=false")
        return False
    
    retry_count = settings.PGVECTOR_RETRY_COUNT
    retry_delay = settings.PGVECTOR_RETRY_DELAY
    
    log.info("pgvector_creation_attempt", retry_count=retry_count, retry_delay=retry_delay)
    
    for attempt in range(1, retry_count + 1):
        try:
            log.info("pgvector_create_attempt", attempt=attempt, total=retry_count)
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            log.info("pgvector_creation_success", attempt=attempt)
            return True
        except Exception as e:
            error_msg = str(e)
            log.warning("pgvector_create_failed", attempt=attempt, total=retry_count, error=error_msg)
            
            # CRITICAL: Rollback the failed transaction to clean up connection state
            try:
                conn.rollback()
                log.debug("pgvector_transaction_rollback", attempt=attempt)
            except Exception as rollback_err:
                log.warning("pgvector_rollback_failed", attempt=attempt, error=str(rollback_err))
            
            if attempt < retry_count:
                log.info("pgvector_retry_wait", delay=retry_delay, next_attempt=attempt + 1)
                import time
                time.sleep(retry_delay)
            else:
                if settings.SKIP_PGVECTOR_ON_FAILURE:
                    log.warning("pgvector_creation_failed_continuing", 
                              message="SKIP_PGVECTOR_ON_FAILURE=true, continuing without vector support",
                              final_error=error_msg)
                    return False
                else:
                    log.error("pgvector_creation_failed_stopping", 
                            message="SKIP_PGVECTOR_ON_FAILURE=false, this will cause migration failure",
                            final_error=error_msg)
                    return False
    
    return False


def _perform_db_introspection(log):
    """Perform comprehensive database introspection with detailed logging."""
    global _LAST_DB_SCHEMA_OK, _LAST_DB_SCHEMA_DETAILS
    
    try:
        with db_session.engine.connect() as conn:  # type: ignore[attr-defined]
            # Check pgvector extension
            try:
                vector_ext = bool(
                    conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar()  # type: ignore[arg-type]
                )
                log.info("pgvector_extension_check", installed=vector_ext)
            except Exception as e:
                vector_ext = False
                log.warning("pgvector_extension_check_failed", error=str(e))

            # Check all required tables
            tables: dict[str, bool] = {}
            required_tables = ("resumes", "resume_text", "resume_chunks", "resume_facts", "jobs")
            
            for t in required_tables:
                try:
                    exists = bool(conn.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": t}).scalar())
                    tables[t] = exists
                    log.info("table_check", table=t, exists=exists)
                except Exception as e:
                    exists = False
                    tables[t] = exists
                    log.warning("table_check_failed", table=t, error=str(e))

            # Check embedding column type (critical for vector functionality)
            try:
                row = conn.execute(
                    text(
                        """
                        SELECT data_type, udt_name
                        FROM information_schema.columns
                        WHERE table_name='resume_chunks' AND column_name='embedding'
                        """
                    )
                ).fetchone()
                embedding_udt = (row[1] if row else None)  # udt_name typically 'vector'
                embedding_data_type = (row[0] if row else None)
                
                if embedding_udt:
                    log.info("embedding_column_check", data_type=embedding_data_type, udt_name=embedding_udt, vector_support=True)
                else:
                    log.warning("embedding_column_check", data_type=embedding_data_type, udt_name=None, vector_support=False, 
                              message="Embedding column not found or not vector type")
            except Exception as e:
                embedding_udt = None
                log.warning("embedding_column_check_failed", error=str(e))

            # Check FTS presence (column + index)
            fts_col, fts_idx = _check_fts_setup(conn, log)

            # Calculate overall schema health
            _LAST_DB_SCHEMA_OK = all(tables.get(t, False) for t in required_tables)
            _LAST_DB_SCHEMA_DETAILS = {
                "vector_extension": vector_ext,
                "tables": tables,
                "embedding_udt": embedding_udt,
                "fts_column": fts_col,
                "fts_index": fts_idx,
            }
            
            # Enhanced logging for schema status
            if not _LAST_DB_SCHEMA_OK:
                missing = [t for t, okv in tables.items() if not okv]
                log.error("db_schema_incomplete", missing=missing, total_tables=len(required_tables), missing_count=len(missing))
            else:
                log.info("db_schema_complete", message="All required tables exist")
            
            # Summary log with all key information
            log.info(
                "postgres_ready",
                vector_extension=vector_ext,
                tables=tables,
                embedding_udt=embedding_udt,
                fts_column=fts_col,
                fts_index=fts_idx,
                schema_ok=_LAST_DB_SCHEMA_OK,
                vector_functionality_available=(vector_ext and embedding_udt == 'vector'),
                search_functionality_available=(fts_col and fts_idx)
            )
            
    except Exception as e:
        log.error("postgres_introspection_failed", error=str(e), message="Failed to perform database introspection")
        _LAST_DB_SCHEMA_OK = None
        _LAST_DB_SCHEMA_DETAILS = None


def _check_fts_setup(conn, log):
    """Check full-text search setup with detailed logging."""
    try:
        fts_col = bool(
            conn.execute(
                text(
                    """
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='resume_text' AND column_name='fts'
                    """
                )
            ).fetchone()
        )
        log.info("fts_column_check", exists=fts_col)
    except Exception as e:
        fts_col = False
        log.warning("fts_column_check_failed", error=str(e))
    
    try:
        fts_idx = bool(
            conn.execute(
                text(
                    """
                    SELECT 1 FROM pg_indexes
                    WHERE tablename='resume_text' AND indexname='resume_text_fts'
                    """
                )
            ).fetchone()
        )
        log.info("fts_index_check", exists=fts_idx)
    except Exception as e:
        fts_idx = False
        log.warning("fts_index_check_failed", error=str(e))
    
    return fts_col, fts_idx


def check_redis() -> bool:
    """Verify Redis connectivity via PING and log readiness."""
    log = get_logger("preflight.redis")
    if _redis is None:
        log.warning("redis_lib_missing")
        return False

    def _probe():
        r = _redis.from_url(settings.REDIS_URL)
        r.ping()

    ok = _retry_until_ok(_probe, name="redis")
    if not ok:
        log.error("redis_unavailable")
        return False

    try:
        r = _redis.from_url(settings.REDIS_URL)
        pong = bool(r.ping())
        log.info("redis_ready", pong=pong)
        return pong
    except Exception as e:
        log.error("redis_check_failed", error=str(e))
        return False


def check_s3() -> bool:
    """Verify S3/MinIO is reachable, buckets exist, and write works on tmp bucket."""
    log = get_logger("preflight.s3")

    def _probe():
        s3 = get_s3_client()
        # lightweight call
        s3.list_buckets()

    ok = _retry_until_ok(_probe, name="s3")
    if not ok:
        log.error("s3_unavailable")
        return False

    buckets_ready = False
    write_ok = False
    try:
        ensure_buckets_existence()
        buckets_ready = True
        # tiny write/delete to tmp bucket to verify perms
        s3 = get_s3_client()
        key = f"preflight-{int(time.time())}.txt"
        s3.put_object(Bucket=settings.S3_BUCKET_TMP, Key=key, Body=b"ok")
        s3.delete_object(Bucket=settings.S3_BUCKET_TMP, Key=key)
        write_ok = True
    except Exception as e:
        log.warning("s3_bucket_or_write_failed", error=str(e))

    log.info(
        "s3_ready",
        endpoint=settings.S3_ENDPOINT.split("//")[-1] if settings.S3_ENDPOINT else None,
        bucket=settings.S3_BUCKET,
        tmp_bucket=settings.S3_BUCKET_TMP,
        buckets_ready=buckets_ready,
        write_test=write_ok,
    )
    return buckets_ready and write_ok


def run_auto_migrations() -> bool:
    """
    Automatically run Alembic migrations to bring database to latest version.
    This ensures the database schema is up-to-date when the application starts.
    """
    log = get_logger("migrations")
    
    if not settings.AUTO_MIGRATE_ON_STARTUP:
        log.info("auto_migration_disabled", message="AUTO_MIGRATE_ON_STARTUP=false, skipping migrations")
        return False
    
    if not ALEMBIC_AVAILABLE:
        log.warning("alembic_not_available", message="Alembic not installed, skipping auto-migrations")
        return False
    
    try:
        log.info("auto_migration_start", message="Running automatic database migrations...")
        
        # Get the Alembic configuration
        alembic_cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic.ini")
        if not os.path.exists(alembic_cfg_path):
            log.error("alembic_config_not_found", path=alembic_cfg_path)
            return False
        
        alembic_cfg = Config(alembic_cfg_path)
        
        # Override the sqlalchemy.url in alembic config with our current DATABASE_URL
        if settings.DATABASE_URL:
            alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            log.info("alembic_config_updated", database_url=settings.DATABASE_URL[:20] + "...")
        
        # Check if this is a fresh database by checking for alembic_version table
        from sqlalchemy import create_engine, text, inspect
        engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
        inspector = inspect(engine)
        
        # Check if alembic_version table exists
        has_alembic_version = inspector.has_table("alembic_version")
        log.info("alembic_version_check", table_exists=has_alembic_version)
        
        if not has_alembic_version:
            # Fresh database - stamp with initial migration
            log.info("fresh_database_detected", message="Stamping database with initial migration")
            command.stamp(alembic_cfg, "base")  # Stamp at base first
        
        # Run the upgrade to head
        log.info("running_migrations", message="Upgrading database to latest schema")
        command.upgrade(alembic_cfg, "head")
        
        # Verify migration success
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            log.info("migration_complete", current_version=version)
        
        engine.dispose()
        log.info("auto_migration_success", message="Database migrations completed successfully")
        return True
        
    except Exception as e:
        log.error("auto_migration_failed", error=str(e), exc_info=True)
        # For fresh deployments, this is a critical failure
        log.error("migration_critical_failure", message="Database schema initialization failed - this will cause 502 errors")
        return False


def run_preflight(level: Optional[str] = None, service: Optional[str] = None, env: Optional[str] = None) -> None:
    """Run all connectivity checks with retries. Non-fatal by default. Prints enhanced summary."""
    configure_logging(level or settings.LOG_LEVEL, service=service or "preflight", env=env or settings.ENV)
    log = get_logger("preflight")
    log.info("start", env=settings.ENV)

    # Import settings to show configuration
    from app.core.config import settings as app_settings
    
    # Log configuration for debugging
    log.info("preflight_config", 
            enable_vector_search=app_settings.ENABLE_VECTOR_SEARCH,
            pgvector_retry_count=app_settings.PGVECTOR_RETRY_COUNT,
            pgvector_retry_delay=app_settings.PGVECTOR_RETRY_DELAY,
            skip_pgvector_on_failure=app_settings.SKIP_PGVECTOR_ON_FAILURE,
            force_pgvector_creation=app_settings.FORCE_PGVECTOR_CREATION)

    # Run automatic database migrations first
    migration_ok = run_auto_migrations()
    
    ok_db = check_postgres()
    ok_redis = check_redis()
    ok_s3 = check_s3()

    log.info("summary", postgres=ok_db, redis=ok_redis, s3=ok_s3, 
             migrations=migration_ok, db_schema_ok=_LAST_DB_SCHEMA_OK)

    # Enhanced human-readable summary for deploy consoles
    try:
        # Basic status line
        print(
            "Preflight summary: Migrations=",
            "OK" if migration_ok else "SKIPPED",
            ", Postgres=",
            "OK" if ok_db else "FAIL",
            " (schema=",
            "OK" if _LAST_DB_SCHEMA_OK else ("UNKNOWN" if _LAST_DB_SCHEMA_OK is None else "INCOMPLETE"),
            "), Redis=",
            "OK" if ok_redis else "FAIL",
            ", S3=",
            "OK" if ok_s3 else "FAIL",
            sep="",
            flush=True,
        )
        
        # Enhanced detailed status for schema issues
        if _LAST_DB_SCHEMA_DETAILS:
            details = _LAST_DB_SCHEMA_DETAILS
            
            # Missing tables
            if _LAST_DB_SCHEMA_OK is False and isinstance(details.get("tables"), dict):
                missing = [t for t, okv in details["tables"].items() if not okv]
                if missing:
                    print(f"📋 DB schema missing: {', '.join(missing)}", flush=True)
                else:
                    print("📋 DB schema: All tables exist but other issues detected", flush=True)
            
            # Vector functionality status
            ve = details.get("vector_extension", False)
            emb = details.get("embedding_udt")
            vector_functional = ve and emb == 'vector'
            
            if ve:
                print(f"🔍 Vector search: ✅ pgvector extension installed, embedding type={emb}", flush=True)
                if vector_functional:
                    print(f"🔍 Vector functionality: ✅ FULLY OPERATIONAL", flush=True)
                else:
                    print(f"🔍 Vector functionality: ⚠️  DEGRADED (embedding column not vector type)", flush=True)
            else:
                print(f"🔍 Vector search: ❌ pgvector extension NOT installed", flush=True)
                print(f"🔍 Vector functionality: ❌ DISABLED (will use text-only search)", flush=True)
            
            # FTS functionality status  
            fts_c = details.get("fts_column", False)
            fts_i = details.get("fts_index", False)
            fts_functional = fts_c and fts_i
            
            if fts_functional:
                print(f"📝 Full-text search: ✅ OPERATIONAL (column + index)", flush=True)
            elif fts_c and not fts_i:
                print(f"📝 Full-text search: ⚠️  DEGRADED (column exists, index missing)", flush=True)
            elif not fts_c:
                print(f"📝 Full-text search: ❌ DISABLED (column missing)", flush=True)
            
            # Configuration summary
            print(f"⚙️  Configuration: vector_search={app_settings.ENABLE_VECTOR_SEARCH}, "
                  f"pgvector_retries={app_settings.PGVECTOR_RETRY_COUNT}, "
                  f"skip_on_failure={app_settings.SKIP_PGVECTOR_ON_FAILURE}", flush=True)
            
            # Overall system capability assessment
            if ok_db and ok_redis and ok_s3:
                if _LAST_DB_SCHEMA_OK and vector_functional:
                    print("🎉 System status: ✅ FULLY OPERATIONAL (all features available)", flush=True)
                elif _LAST_DB_SCHEMA_OK and not vector_functional:
                    print("🔄 System status: ⚠️  OPERATIONAL WITH LIMITATIONS (vector search disabled)", flush=True)
                elif not _LAST_DB_SCHEMA_OK:
                    print("🚧 System status: ⚠️  PARTIAL (schema incomplete, some features unavailable)", flush=True)
            else:
                failed_services = []
                if not ok_db: failed_services.append("Database")
                if not ok_redis: failed_services.append("Redis") 
                if not ok_s3: failed_services.append("S3")
                print(f"💥 System status: ❌ DEGRADED ({', '.join(failed_services)} connectivity issues)", flush=True)
        
        else:
            # Fallback if no details available
            print(f"pgvector=unknown, embedding_udt=unknown, fts_column=unknown, fts_index=unknown", flush=True)
            
    except Exception as e:
        print(f"Error generating preflight summary: {str(e)}", flush=True)

    log.info("done")


# ---------- Lightweight health snapshots for runtime (non-mutating, no retries) ----------

def db_status_snapshot() -> dict:
    """Return current DB status without altering schema or performing retries."""
    out = {
        "reachable": False,
        "schema_ok": None,
        "vector_extension": None,
        "embedding_udt": None,
        "fts_column": None,
        "fts_index": None,
        "tables": {},
    }
    try:
        with db_session.engine.connect() as conn:  # type: ignore[attr-defined]
            conn.execute(text("SELECT 1"))
            out["reachable"] = True
            try:
                out["vector_extension"] = bool(
                    conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')")).scalar()  # type: ignore[arg-type]
                )
            except Exception:
                out["vector_extension"] = False

            tables: dict[str, bool] = {}
            for t in ("resumes", "resume_text", "resume_chunks", "resume_facts", "jobs"):
                try:
                    exists = bool(conn.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": t}).scalar())
                except Exception:
                    exists = False
                tables[t] = exists
            out["tables"] = tables

            try:
                row = conn.execute(
                    text(
                        """
                        SELECT data_type, udt_name
                        FROM information_schema.columns
                        WHERE table_name='resume_chunks' AND column_name='embedding'
                        """
                    )
                ).fetchone()
                out["embedding_udt"] = (row[1] if row else None)
            except Exception:
                out["embedding_udt"] = None

            try:
                out["fts_column"] = bool(
                    conn.execute(
                        text(
                            """
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='resume_text' AND column_name='fts'
                            """
                        )
                    ).fetchone()
                )
            except Exception:
                out["fts_column"] = False
            try:
                out["fts_index"] = bool(
                    conn.execute(
                        text(
                            """
                            SELECT 1 FROM pg_indexes
                            WHERE tablename='resume_text' AND indexname='resume_text_fts'
                            """
                        )
                    ).fetchone()
                )
            except Exception:
                out["fts_index"] = False

            out["schema_ok"] = all(tables.get(t, False) for t in ("resumes", "resume_text", "resume_chunks", "resume_facts"))
    except Exception:
        # unreachable DB
        pass
    return out


def redis_status_snapshot() -> dict:
    out = {"reachable": False, "pong": None}
    if _redis is None:
        return out
    try:
        r = _redis.from_url(settings.REDIS_URL)
        out["pong"] = bool(r.ping())
        out["reachable"] = bool(out["pong"])  # True only if PING succeeded
    except Exception:
        pass
    return out


def s3_status_snapshot() -> dict:
    out = {
        "reachable": False,
        "endpoint": settings.S3_ENDPOINT.split("//")[-1] if settings.S3_ENDPOINT else None,
        "buckets": {
            settings.S3_BUCKET: None,
            settings.S3_BUCKET_TMP: None,
        },
    }
    try:
        s3 = get_s3_client()
        # reachability
        s3.list_buckets()
        out["reachable"] = True
        # bucket existence without creating
        for b in (settings.S3_BUCKET, settings.S3_BUCKET_TMP):
            try:
                s3.head_bucket(Bucket=b)
                out["buckets"][b] = True
            except Exception:
                out["buckets"][b] = False
    except Exception:
        pass
    return out


def main():
    """Main entry point for preflight checks when run as module"""
    configure_logging(settings.LOG_LEVEL, service="preflight", env=settings.ENV)
    log = get_logger("preflight.main")
    
    log.info("preflight_start", message="Starting Railway deployment preflight checks")
    
    try:
        # Run database migrations first
        log.info("preflight_migrations", message="Running automatic database migrations")
        migration_ok = run_auto_migrations()
        
        # Check database status
        log.info("preflight_database", message="Checking database status")
        db_status = db_status_snapshot()
        db_ok = db_status.get("reachable", False)
        
        # Quick checks for other services (non-blocking)
        log.info("preflight_redis", message="Checking Redis connectivity")
        redis_status = redis_status_snapshot()
        
        log.info("preflight_s3", message="Checking S3/MinIO connectivity")
        s3_status = s3_status_snapshot()
        
        # Summary
        summary = {
            "migration_success": migration_ok,
            "database_ready": db_ok,
            "redis_reachable": redis_status.get("reachable", False),
            "s3_reachable": s3_status.get("reachable", False),
        }
        
        log.info("preflight_complete", summary=summary)
        
        if migration_ok and db_ok:
            log.info("preflight_success", message="✅ Preflight checks completed successfully")
            return 0
        elif not migration_ok:
            log.error("preflight_migration_failure", message="❌ Critical failure: Database migrations failed")
            log.error("deployment_blocked", message="🚨 Deployment cannot continue without database schema")
            return 1  # Return error code for migration failures
        elif not db_ok:
            log.error("preflight_database_failure", message="❌ Critical failure: Database connectivity failed")
            log.error("deployment_blocked", message="🚨 Deployment cannot continue without database access")
            return 1  # Return error code for database failures
        else:
            log.warning("preflight_partial", message="⚠️ Preflight completed with some issues", 
                       migration_ok=migration_ok, db_ok=db_ok)
            return 0  # Continue for non-critical issues
            
    except Exception as e:
        log.error("preflight_error", error=str(e), exc_info=True)
        log.error("preflight_exception", message="❌ Critical preflight exception - deployment blocked")
        return 1  # Return error code for exceptions


if __name__ == "__main__":
    import sys
    sys.exit(main())
