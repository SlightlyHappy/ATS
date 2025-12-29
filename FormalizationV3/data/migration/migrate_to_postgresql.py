#!/usr/bin/env python3
"""
Data Migration Script: SQLite to PostgreSQL
Generated on: 2025-07-29 12:31:26.236137
"""

import sqlite3
import psycopg2
import logging
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self, sqlite_path: str, pg_config: Dict[str, Any]):
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
    
    def migrate_data(self):
        """Migrate all data from SQLite to PostgreSQL"""
        try:
            # Connect to both databases
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            pg_conn = psycopg2.connect(**self.pg_config)
            
            # Get all tables
            cursor = sqlite_conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            for table_name in tables:
                self.migrate_table(sqlite_conn, pg_conn, table_name)
            
            pg_conn.commit()
            logger.info("Data migration completed successfully")
            
        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            if 'pg_conn' in locals():
                pg_conn.rollback()
            raise
        finally:
            if 'sqlite_conn' in locals():
                sqlite_conn.close()
            if 'pg_conn' in locals():
                pg_conn.close()
    
    def migrate_table(self, sqlite_conn, pg_conn, table_name: str):
        """Migrate a single table"""
        try:
            # Get table data from SQLite
            sqlite_cursor = sqlite_conn.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                logger.info(f"Table {table_name} is empty, skipping")
                return
            
            # Get column names
            columns = [description[0] for description in sqlite_cursor.description]
            
            # Prepare PostgreSQL insert
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            
            # Insert data into PostgreSQL
            pg_cursor = pg_conn.cursor()
            for row in rows:
                pg_cursor.execute(insert_sql, tuple(row))
            
            logger.info(f"Migrated {len(rows)} rows from {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to migrate table {table_name}: {e}")
            raise

if __name__ == "__main__":
    # Configuration
    SQLITE_PATH = "data/local.db"
    PG_CONFIG = {
        'host': os.getenv('PGHOST'),
        'port': os.getenv('PGPORT', 5432),
        'database': os.getenv('PGDATABASE'),
        'user': os.getenv('PGUSER'),
        'password': os.getenv('PGPASSWORD')
    }
    
    migrator = DataMigrator(SQLITE_PATH, PG_CONFIG)
    migrator.migrate_data()
