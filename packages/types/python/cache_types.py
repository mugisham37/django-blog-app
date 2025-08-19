"""
Cache-related Python type definitions
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Union
from datetime import datetime
from dataclasses import dataclass


class CacheProvider(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"
    DATABASE = "database"
    FILE = "file"
    HYBRID = "hybrid"


class CacheStrategy(str, Enum):
    CACHE_ASIDE = "cache_aside"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


class CacheEvictionPolicy(str, Enum):
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    TTL = "ttl"  # Time To Live
    RANDOM = "random"


@dataclass
class CacheConfig:
    """Cache configuration"""
    provider: CacheProvider = CacheProvider.MEMORY
    strategy: CacheStrategy = CacheStrategy.CACHE_ASIDE
    eviction_policy: CacheEvictionPolicy = CacheEvictionPolicy.LRU
    default_ttl: int = 3600  # in seconds
    max_size: int = 1000  # in bytes or items
    compression: bool = False
    serialization: str = "json"  # json, msgpack, pickle
    key_prefix: str = ""
    namespace: str = "default"


@dataclass
class CacheKey:
    """Cache key"""
    namespace: str
    key: str
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class CacheEntry:
    """Cache entry"""
    key: str
    value: Any
    ttl: int
    created_at: float
    accessed_at: float
    access_count: int = 0
    size: int = 0
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CacheOperationResult:
    """Cache operation result"""
    success: bool
    data: Optional[Any] = None
    hit: bool = False
    ttl: Optional[int] = None
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    hit_rate: float = 0.0
    total_operations: int = 0
    total_size: int = 0
    entry_count: int = 0
    evictions: int = 0
    expired_entries: int = 0
    average_ttl: float = 0.0
    memory_usage: int = 0


@dataclass
class RedisCacheConfig(CacheConfig):
    """Redis cache configuration"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0
    cluster: bool = False
    cluster_nodes: Optional[List[Dict[str, Union[str, int]]]] = None
    connection_pool: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.cluster_nodes is None:
            self.cluster_nodes = []
        if self.connection_pool is None:
            self.connection_pool = {
                "min_connections": 1,
                "max_connections": 10,
                "idle_timeout": 300,
            }


@dataclass
class MemoryCacheConfig(CacheConfig):
    """Memory cache configuration"""
    max_memory: int = 100 * 1024 * 1024  # 100MB in bytes
    cleanup_interval: int = 60  # in seconds
    stats_interval: int = 300  # in seconds


@dataclass
class DatabaseCacheConfig(CacheConfig):
    """Database cache configuration"""
    table_name: str = "cache_entries"
    connection_string: str = ""
    cleanup_interval: int = 3600
    index_keys: bool = True


@dataclass
class CacheDecoratorOptions:
    """Cache decorator options"""
    key: Optional[Union[str, Callable]] = None
    ttl: Optional[int] = None
    tags: Optional[Union[List[str], Callable]] = None
    condition: Optional[Callable] = None
    unless: Optional[Callable] = None
    serialize: bool = True
    compress: bool = False


@dataclass
class CacheInvalidationOptions:
    """Cache invalidation options"""
    keys: Optional[List[str]] = None
    patterns: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    namespace: Optional[str] = None
    cascade: bool = False


@dataclass
class CacheWarmingStrategy:
    """Cache warming strategy"""
    name: str
    schedule: str  # cron expression
    keys: Union[List[str], Callable] = None
    loader: Callable = None
    ttl: Optional[int] = None


@dataclass
class CacheWarmingConfig:
    """Cache warming configuration"""
    enabled: bool = False
    strategies: List[CacheWarmingStrategy] = None
    
    def __post_init__(self):
        if self.strategies is None:
            self.strategies = []


@dataclass
class CacheMonitoringConfig:
    """Cache monitoring configuration"""
    enabled: bool = True
    metrics_interval: int = 60  # in seconds
    alert_thresholds: Dict[str, float] = None
    export_metrics: bool = False
    metrics_endpoint: Optional[str] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                "hit_rate_min": 0.8,
                "memory_usage_max": 0.9,
                "error_rate_max": 0.05,
                "response_time_max": 100.0,
            }


@dataclass
class CacheLayerConfig:
    """Cache layer configuration for multi-level caching"""
    name: str
    provider: CacheProvider
    config: CacheConfig
    priority: int = 0
    read_through: bool = True
    write_through: bool = True
    fallback: bool = False


@dataclass
class MultiLevelCacheConfig:
    """Multi-level cache configuration"""
    layers: List[CacheLayerConfig] = None
    default_layer: str = "memory"
    promotion_policy: str = "lru"  # lru, lfu, manual
    consistency_mode: str = "eventual"  # eventual, strong
    
    def __post_init__(self):
        if self.layers is None:
            self.layers = []


class CacheEventType(str, Enum):
    HIT = "hit"
    MISS = "miss"
    SET = "set"
    DELETE = "delete"
    EVICT = "evict"
    EXPIRE = "expire"
    CLEAR = "clear"
    ERROR = "error"


@dataclass
class CacheEvent:
    """Cache event"""
    type: CacheEventType
    key: str
    namespace: str
    timestamp: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CacheHealthCheck:
    """Cache health check"""
    provider: CacheProvider
    status: str = "healthy"  # healthy, unhealthy, degraded
    response_time: float = 0.0
    error_rate: float = 0.0
    memory_usage: float = 0.0
    connection_count: int = 0
    last_check: float = 0.0


@dataclass
class CacheBackupConfig:
    """Cache backup configuration"""
    enabled: bool = False
    schedule: str = "0 2 * * *"  # cron expression
    destination: str = ""
    compression: bool = True
    encryption: bool = False
    retention_days: int = 7


@dataclass
class CacheRestoreConfig:
    """Cache restore configuration"""
    source: str
    overwrite_existing: bool = False
    verify_integrity: bool = True
    batch_size: int = 1000


@dataclass
class DistributedCacheConfig(CacheConfig):
    """Distributed cache configuration"""
    nodes: List[Dict[str, Union[str, int, float]]] = None
    replication_factor: int = 1
    consistency_level: str = "one"  # one, quorum, all
    partition_strategy: str = "hash"  # hash, range, consistent_hash
    failure_detection: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
        if self.failure_detection is None:
            self.failure_detection = {
                "enabled": True,
                "timeout": 5000,
                "retry_attempts": 3,
            }