"""
PostgreSQL-based Knowledge Gap Database

Unified database for knowledge gap detection across Clara, Veritas, and Covina.
Replaces file-based storage with centralized PostgreSQL table.

Features:
- Shared table for all systems (Clara, Veritas, Covina)
- Source tracking to identify origin system
- Full SQL query capabilities
- Transaction support
- Concurrent access safe
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor, Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logging.warning("psycopg2 not available - PostgreSQL knowledge gap database disabled")

from .knowledge_gaps import KnowledgeGap, GapSeverity, GapSource

logger = logging.getLogger(__name__)


class SystemSource(str, Enum):
    """System that detected the knowledge gap"""
    CLARA = "clara"
    VERITAS = "veritas"
    COVINA = "covina"


class KnowledgeGapPostgreSQLDatabase:
    """
    PostgreSQL-based Knowledge Gap Database
    
    Unified database for knowledge gaps from Clara, Veritas, and Covina.
    Uses a single table with source tracking.
    
    Table Schema:
        - gap_id (PK): Unique identifier
        - system_source: System that detected gap (clara/veritas/covina)
        - domain: Domain/specialty
        - adapter_id: Related adapter
        - topic: Specific topic/area
        - severity: Critical/High/Medium/Low
        - source: Detection source (evaluation/training/inference)
        - prompt: Input that failed
        - expected_output: Expected response
        - actual_output: Adapter's response
        - confidence_score: 0-1
        - evaluation_score: 0-100
        - detected_at: Timestamp
        - detected_by: User/system that detected
        - tags: JSON array
        - status: open/in_progress/resolved
        - resolved_at: Timestamp
        - resolution_notes: Text
        - requires_training_data: Boolean
        - suggested_data_query: Text
        - training_samples_collected: Integer
        - metadata: JSON object
    """
    
    def __init__(
        self,
        host: str = "192.168.178.94",
        port: int = 5432,
        user: str = "postgres",
        password: str = "postgres",
        database: str = "postgres",
        schema: str = "public"
    ):
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 not installed. Install with: pip install psycopg2-binary")
        
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.schema = schema
        self.table_name = "knowledge_gaps"
        
        # Create table if not exists
        self._create_table()
        
        logger.info(
            f"📚 PostgreSQL KnowledgeGapDatabase initialized: "
            f"{host}:{port}/{database}.{schema}.{self.table_name}"
        )
    
    def _get_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )
    
    def _create_table(self):
        """Create knowledge_gaps table if not exists"""
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.schema}.{self.table_name} (
            gap_id VARCHAR(255) PRIMARY KEY,
            system_source VARCHAR(50) NOT NULL,
            domain VARCHAR(255) NOT NULL,
            adapter_id VARCHAR(255),
            topic TEXT NOT NULL,
            severity VARCHAR(50) NOT NULL,
            source VARCHAR(50) NOT NULL,
            prompt TEXT,
            expected_output TEXT,
            actual_output TEXT,
            confidence_score FLOAT,
            evaluation_score FLOAT,
            detected_at TIMESTAMP NOT NULL DEFAULT NOW(),
            detected_by VARCHAR(255),
            tags JSONB DEFAULT '[]'::jsonb,
            status VARCHAR(50) NOT NULL DEFAULT 'open',
            resolved_at TIMESTAMP,
            resolution_notes TEXT,
            requires_training_data BOOLEAN DEFAULT TRUE,
            suggested_data_query TEXT,
            training_samples_collected INTEGER DEFAULT 0,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
        
        -- Indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_system_source 
            ON {self.schema}.{self.table_name}(system_source);
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_domain 
            ON {self.schema}.{self.table_name}(domain);
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_severity 
            ON {self.schema}.{self.table_name}(severity);
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_status 
            ON {self.schema}.{self.table_name}(status);
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_detected_at 
            ON {self.schema}.{self.table_name}(detected_at DESC);
        
        -- Composite indexes for common filter combinations
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_system_status 
            ON {self.schema}.{self.table_name}(system_source, status);
        CREATE INDEX IF NOT EXISTS idx_knowledge_gaps_domain_status 
            ON {self.schema}.{self.table_name}(domain, status);
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_sql)
                conn.commit()
            logger.info(f"✅ Table {self.schema}.{self.table_name} ready")
        except Exception as e:
            logger.error(f"Failed to create table: {e}")
            raise
    
    def add_gap(
        self,
        gap: KnowledgeGap,
        system_source: SystemSource = SystemSource.CLARA
    ):
        """
        Add knowledge gap to database
        
        Args:
            gap: Knowledge gap to add
            system_source: System that detected the gap (clara/veritas/covina)
        """
        insert_sql = f"""
        INSERT INTO {self.schema}.{self.table_name} (
            gap_id, system_source, domain, adapter_id, topic, severity, source,
            prompt, expected_output, actual_output, confidence_score, evaluation_score,
            detected_at, detected_by, tags, status, requires_training_data,
            suggested_data_query, training_samples_collected, metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (gap_id) DO UPDATE SET
            system_source = EXCLUDED.system_source,
            domain = EXCLUDED.domain,
            adapter_id = EXCLUDED.adapter_id,
            topic = EXCLUDED.topic,
            severity = EXCLUDED.severity,
            source = EXCLUDED.source,
            prompt = EXCLUDED.prompt,
            expected_output = EXCLUDED.expected_output,
            actual_output = EXCLUDED.actual_output,
            confidence_score = EXCLUDED.confidence_score,
            evaluation_score = EXCLUDED.evaluation_score,
            detected_by = EXCLUDED.detected_by,
            tags = EXCLUDED.tags,
            suggested_data_query = EXCLUDED.suggested_data_query,
            updated_at = NOW()
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(insert_sql, (
                        gap.gap_id,
                        system_source.value,
                        gap.domain,
                        gap.adapter_id,
                        gap.topic,
                        gap.severity.value,
                        gap.source.value,
                        gap.prompt,
                        gap.expected_output,
                        gap.actual_output,
                        gap.confidence_score,
                        gap.evaluation_score,
                        gap.detected_at,
                        gap.detected_by,
                        Json(gap.tags),
                        gap.status,
                        gap.requires_training_data,
                        gap.suggested_data_query,
                        gap.training_samples_collected,
                        Json({})  # metadata
                    ))
                conn.commit()
            
            logger.info(f"✅ Added gap to database: {gap.gap_id} (source: {system_source.value})")
        
        except Exception as e:
            logger.error(f"Failed to add gap: {e}")
            raise
    
    def add_gaps(
        self,
        gaps: List[KnowledgeGap],
        system_source: SystemSource = SystemSource.CLARA
    ):
        """
        Add multiple knowledge gaps to database (batch insert)
        
        Args:
            gaps: List of knowledge gaps
            system_source: System that detected the gaps
        """
        if not gaps:
            return
        
        for gap in gaps:
            self.add_gap(gap, system_source)
        
        logger.info(f"✅ Added {len(gaps)} gaps to database (source: {system_source.value})")
    
    def get_gaps(
        self,
        domain: Optional[str] = None,
        adapter_id: Optional[str] = None,
        severity: Optional[GapSeverity] = None,
        status: Optional[str] = None,
        system_source: Optional[SystemSource] = None,
        limit: Optional[int] = None
    ) -> List[KnowledgeGap]:
        """
        Get knowledge gaps with filters
        
        Args:
            domain: Filter by domain
            adapter_id: Filter by adapter
            severity: Filter by severity
            status: Filter by status (default: all)
            system_source: Filter by system (clara/veritas/covina)
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge gaps
        """
        # Build query with filters
        where_clauses = []
        params = []
        
        if domain:
            where_clauses.append("domain = %s")
            params.append(domain)
        
        if adapter_id:
            where_clauses.append("adapter_id = %s")
            params.append(adapter_id)
        
        if severity:
            where_clauses.append("severity = %s")
            params.append(severity.value)
        
        if status:
            where_clauses.append("status = %s")
            params.append(status)
        
        if system_source:
            where_clauses.append("system_source = %s")
            params.append(system_source.value)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        limit_sql = f"LIMIT {limit}" if limit else ""
        
        select_sql = f"""
        SELECT gap_id, system_source, domain, adapter_id, topic, severity, source,
               prompt, expected_output, actual_output, confidence_score, evaluation_score,
               detected_at, detected_by, tags, status, resolved_at, resolution_notes,
               requires_training_data, suggested_data_query, training_samples_collected
        FROM {self.schema}.{self.table_name}
        WHERE {where_sql}
        ORDER BY detected_at DESC
        {limit_sql}
        """
        
        gaps = []
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(select_sql, params)
                    rows = cur.fetchall()
                    
                    for row in rows:
                        # Convert to KnowledgeGap
                        gap = KnowledgeGap(
                            gap_id=row['gap_id'],
                            domain=row['domain'],
                            adapter_id=row['adapter_id'],
                            topic=row['topic'],
                            severity=GapSeverity(row['severity']),
                            source=GapSource(row['source']),
                            prompt=row['prompt'],
                            expected_output=row['expected_output'],
                            actual_output=row['actual_output'],
                            confidence_score=row['confidence_score'],
                            evaluation_score=row['evaluation_score'],
                            detected_at=row['detected_at'],
                            detected_by=row['detected_by'],
                            tags=row['tags'] or [],
                            status=row['status'],
                            resolved_at=row['resolved_at'],
                            resolution_notes=row['resolution_notes'],
                            requires_training_data=row['requires_training_data'],
                            suggested_data_query=row['suggested_data_query'],
                            training_samples_collected=row['training_samples_collected']
                        )
                        gaps.append(gap)
        
        except Exception as e:
            logger.error(f"Failed to get gaps: {e}")
            return []
        
        return gaps
    
    def get_priority_gaps(
        self,
        top_n: int = 10,
        system_source: Optional[SystemSource] = None
    ) -> List[KnowledgeGap]:
        """
        Get highest priority gaps
        
        Args:
            top_n: Number of top gaps to return
            system_source: Filter by system (optional)
            
        Returns:
            List of gaps sorted by priority
        """
        gaps = self.get_gaps(status="open", system_source=system_source)
        
        # Sort by priority
        gaps.sort(key=lambda g: g.calculate_priority(), reverse=True)
        
        return gaps[:top_n]
    
    def update_gap_status(
        self,
        gap_id: str,
        status: str,
        resolution_notes: Optional[str] = None
    ):
        """
        Update gap status
        
        Args:
            gap_id: Gap identifier
            status: New status (open/in_progress/resolved)
            resolution_notes: Optional notes
        """
        update_sql = f"""
        UPDATE {self.schema}.{self.table_name}
        SET status = %s,
            resolved_at = CASE WHEN %s = 'resolved' THEN NOW() ELSE NULL END,
            resolution_notes = COALESCE(%s, resolution_notes),
            updated_at = NOW()
        WHERE gap_id = %s
        """
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(update_sql, (status, status, resolution_notes, gap_id))
                conn.commit()
            
            logger.info(f"✅ Updated gap status: {gap_id} → {status}")
        
        except Exception as e:
            logger.error(f"Failed to update gap status: {e}")
            raise
    
    def get_statistics(
        self,
        system_source: Optional[SystemSource] = None
    ) -> Dict[str, Any]:
        """
        Get knowledge gap statistics
        
        Args:
            system_source: Filter by system (optional)
            
        Returns:
            Dictionary with statistics
        """
        where_sql = f"WHERE system_source = '{system_source.value}'" if system_source else ""
        
        stats_sql = f"""
        SELECT
            COUNT(*) as total_gaps,
            COUNT(*) FILTER (WHERE status = 'open') as open_gaps,
            COUNT(*) FILTER (WHERE status = 'resolved') as resolved_gaps,
            COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
            AVG(evaluation_score) as avg_score
        FROM {self.schema}.{self.table_name}
        {where_sql}
        """
        
        severity_sql = f"""
        SELECT severity, COUNT(*) as count
        FROM {self.schema}.{self.table_name}
        {where_sql}
        GROUP BY severity
        """
        
        domain_sql = f"""
        SELECT domain, COUNT(*) as count
        FROM {self.schema}.{self.table_name}
        {where_sql}
        GROUP BY domain
        ORDER BY count DESC
        LIMIT 10
        """
        
        source_sql = f"""
        SELECT source, COUNT(*) as count
        FROM {self.schema}.{self.table_name}
        {where_sql}
        GROUP BY source
        """
        
        system_sql = f"""
        SELECT system_source, COUNT(*) as count
        FROM {self.schema}.{self.table_name}
        GROUP BY system_source
        """
        
        stats = {}
        
        try:
            with self._get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # General stats
                    cur.execute(stats_sql)
                    row = cur.fetchone()
                    stats.update(dict(row))
                    
                    # By severity
                    cur.execute(severity_sql)
                    stats['by_severity'] = {row['severity']: row['count'] for row in cur.fetchall()}
                    
                    # By domain
                    cur.execute(domain_sql)
                    stats['by_domain'] = {row['domain']: row['count'] for row in cur.fetchall()}
                    
                    # By source
                    cur.execute(source_sql)
                    stats['by_source'] = {row['source']: row['count'] for row in cur.fetchall()}
                    
                    # By system (only if not filtering by system)
                    if not system_source:
                        cur.execute(system_sql)
                        stats['by_system'] = {row['system_source']: row['count'] for row in cur.fetchall()}
        
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
        
        return stats


# Global instance
_knowledge_gap_pg_database = None


def get_knowledge_gap_pg_database(
    host: Optional[str] = None,
    port: Optional[int] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None
) -> KnowledgeGapPostgreSQLDatabase:
    """
    Get global PostgreSQL knowledge gap database instance
    
    Args:
        host: PostgreSQL host (default: from config)
        port: PostgreSQL port (default: from config)
        user: PostgreSQL user (default: from config)
        password: PostgreSQL password (default: from config)
        database: PostgreSQL database (default: from config)
        schema: PostgreSQL schema (default: public)
        
    Returns:
        Shared database instance
    """
    global _knowledge_gap_pg_database
    
    if _knowledge_gap_pg_database is None:
        # Get config from base config if available
        try:
            from config.base import get_config
            config = get_config()
            _knowledge_gap_pg_database = KnowledgeGapPostgreSQLDatabase(
                host=host or config.postgres_host,
                port=port or config.postgres_port,
                user=user or config.postgres_user,
                password=password or config.postgres_password,
                database=database or config.postgres_database,
                schema=schema or config.postgres_schema
            )
        except Exception as e:
            logger.warning(f"Could not load config, using defaults: {e}")
            _knowledge_gap_pg_database = KnowledgeGapPostgreSQLDatabase(
                host=host or "192.168.178.94",
                port=port or 5432,
                user=user or "postgres",
                password=password or "postgres",
                database=database or "postgres",
                schema=schema or "public"
            )
    
    return _knowledge_gap_pg_database
