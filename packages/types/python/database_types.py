"""
Database-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Union, Callable
from datetime import datetime
from dataclasses import dataclass


class DatabaseProvider(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    REDIS = "redis"


class IsolationLevel(str, Enum):
    READ_UNCOMMITTED = "read_uncommitted"
    READ_COMMITTED = "read_committed"
    REPEATABLE_READ = "repeatable_read"
    SERIALIZABLE = "serializable"


class DatabaseEventType(str, Enum):
    CONNECTION_OPENED = "connection_opened"
    CONNECTION_CLOSED = "connection_closed"
    QUERY_EXECUTED = "query_executed"
    TRANSACTION_STARTED = "transaction_started"
    TRANSACTION_COMMITTED = "transaction_committed"
    TRANSACTION_ROLLED_BACK = "transaction_rolled_back"
    MIGRATION_APPLIED = "migration_applied"
    BACKUP_COMPLETED = "backup_completed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""
    min_connections: int = 1
    max_connections: int = 10
    idle_timeout: int = 300  # in seconds
    connection_timeout: int = 30  # in seconds
    validation_query: str = "SELECT 1"
    test_on_borrow: bool = True
    test_on_return: bool = False
    test_while_idle: bool = True


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    provider: DatabaseProvider = DatabaseProvider.POSTGRESQL
    host: str = "localhost"
    port: int = 5432
    database: str = ""
    username: str = ""
    password: str = ""
    ssl: bool = False
    pool: ConnectionPoolConfig = None
    read_replicas: Optional[List[Dict[str, Union[str, int, float]]]] = None
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.pool is None:
            self.pool = ConnectionPoolConfig()
        if self.read_replicas is None:
            self.read_replicas = []
        if self.options is None:
            self.options = {}


@dataclass
class QueryResult:
    """Query result"""
    rows: List[Any] = None
    row_count: int = 0
    affected_rows: int = 0
    execution_time: float = 0.0
    query: str = ""
    parameters: List[Any] = None
    
    def __post_init__(self):
        if self.rows is None:
            self.rows = []
        if self.parameters is None:
            self.parameters = []


@dataclass
class FindOptions:
    """Find options"""
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: Optional[List[Dict[str, str]]] = None
    include: Optional[List[str]] = None
    select: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.order_by is None:
            self.order_by = []
        if self.include is None:
            self.include = []
        if self.select is None:
            self.select = []


@dataclass
class MigrationStatus:
    """Migration status"""
    version: str
    name: str
    applied_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    status: str = "pending"  # pending, applied, failed
    error: Optional[str] = None


@dataclass
class ConnectionStats:
    """Connection statistics"""
    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    queries_executed: int = 0
    average_query_time: float = 0.0
    errors_count: int = 0
    uptime: float = 0.0


@dataclass
class ColumnDefinition:
    """Column definition"""
    name: str
    type: str
    nullable: bool = True
    default_value: Optional[Any] = None
    auto_increment: bool = False
    primary_key: bool = False
    unique: bool = False
    foreign_key: Optional[Dict[str, str]] = None


@dataclass
class IndexDefinition:
    """Index definition"""
    name: str
    columns: List[str]
    unique: bool = False
    type: str = "btree"  # btree, hash, gin, gist
    where: Optional[str] = None


@dataclass
class ConstraintDefinition:
    """Constraint definition"""
    name: str
    type: str  # primary_key, foreign_key, unique, check
    columns: List[str]
    reference: Optional[Dict[str, List[str]]] = None
    check_expression: Optional[str] = None


@dataclass
class TriggerDefinition:
    """Trigger definition"""
    name: str
    event: str  # INSERT, UPDATE, DELETE
    timing: str  # BEFORE, AFTER, INSTEAD OF
    function_name: str
    condition: Optional[str] = None


@dataclass
class TableSchema:
    """Database schema definition"""
    name: str
    columns: List[ColumnDefinition]
    indexes: List[IndexDefinition] = None
    constraints: List[ConstraintDefinition] = None
    triggers: Optional[List[TriggerDefinition]] = None
    
    def __post_init__(self):
        if self.indexes is None:
            self.indexes = []
        if self.constraints is None:
            self.constraints = []
        if self.triggers is None:
            self.triggers = []


@dataclass
class SeedData:
    """Seed data interface"""
    table: str
    data: List[Dict[str, Any]]
    truncate_before: bool = False
    update_on_conflict: bool = False
    conflict_columns: Optional[List[str]] = None


@dataclass
class BackupConfig:
    """Database backup configuration"""
    enabled: bool = False
    schedule: str = "0 2 * * *"  # cron expression
    destination: str = ""
    compression: bool = True
    encryption: bool = False
    retention_days: int = 30
    include_tables: Optional[List[str]] = None
    exclude_tables: Optional[List[str]] = None


@dataclass
class DatabaseMetrics:
    """Database monitoring metrics"""
    connections: Dict[str, int] = None
    queries: Dict[str, Union[int, float]] = None
    performance: Dict[str, float] = None
    replication: Dict[str, Union[int, float, str]] = None
    
    def __post_init__(self):
        if self.connections is None:
            self.connections = {
                "active": 0,
                "idle": 0,
                "total": 0,
                "max_used": 0,
            }
        if self.queries is None:
            self.queries = {
                "total": 0,
                "per_second": 0.0,
                "average_duration": 0.0,
                "slow_queries": 0,
            }
        if self.performance is None:
            self.performance = {
                "cpu_usage": 0.0,
                "memory_usage": 0.0,
                "disk_usage": 0.0,
                "cache_hit_ratio": 0.0,
            }
        if self.replication is None:
            self.replication = {
                "lag": 0.0,
                "status": "healthy",
                "replicas_count": 0,
            }


@dataclass
class QueryPerformanceStats:
    """Query performance statistics"""
    query_hash: str
    query_template: str
    execution_count: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    min_time: float = 0.0
    max_time: float = 0.0
    rows_examined: int = 0
    rows_sent: int = 0
    last_executed: datetime = None


@dataclass
class DatabaseHealthCheck:
    """Database health check"""
    status: str = "healthy"  # healthy, unhealthy, degraded
    response_time: float = 0.0
    connection_status: bool = True
    replication_status: bool = True
    disk_space: Dict[str, Union[int, float]] = None
    last_backup: Optional[datetime] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.disk_space is None:
            self.disk_space = {
                "total": 0,
                "used": 0,
                "available": 0,
                "usage_percentage": 0.0,
            }
        if self.errors is None:
            self.errors = []


@dataclass
class BulkOperationConfig:
    """Bulk operation configuration"""
    batch_size: int = 1000
    parallel_batches: int = 1
    continue_on_error: bool = False
    progress_callback: Optional[Callable] = None


@dataclass
class BulkInsertResult:
    """Bulk insert result"""
    inserted_count: int = 0
    failed_count: int = 0
    errors: List[Dict[str, Union[int, str]]] = None
    execution_time: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class DatabaseEvent:
    """Database event"""
    type: DatabaseEventType
    timestamp: float
    connection_id: Optional[str] = None
    query: Optional[str] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ReadWriteSplitConfig:
    """Read/Write splitting configuration"""
    enabled: bool = False
    read_replicas: List[Dict[str, Union[str, int, float]]] = None
    load_balancing: str = "round_robin"  # round_robin, weighted, least_connections
    failover: Dict[str, Union[bool, int]] = None
    
    def __post_init__(self):
        if self.read_replicas is None:
            self.read_replicas = []
        if self.failover is None:
            self.failover = {
                "enabled": True,
                "timeout": 5000,
                "retry_attempts": 3,
            }


@dataclass
class ShardingConfig:
    """Sharding configuration"""
    enabled: bool = False
    strategy: str = "hash"  # hash, range, directory
    shards: List[Dict[str, Any]] = None
    shard_key: str = "id"
    
    def __post_init__(self):
        if self.shards is None:
            self.shards = []