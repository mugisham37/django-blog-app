/**
 * Cache-related type definitions
 */

// Cache provider types
export enum CacheProvider {
  MEMORY = "memory",
  REDIS = "redis",
  DATABASE = "database",
  FILE = "file",
  HYBRID = "hybrid",
}

// Cache strategy types
export enum CacheStrategy {
  CACHE_ASIDE = "cache_aside",
  WRITE_THROUGH = "write_through",
  WRITE_BEHIND = "write_behind",
  REFRESH_AHEAD = "refresh_ahead",
}

// Cache eviction policies
export enum CacheEvictionPolicy {
  LRU = "lru", // Least Recently Used
  LFU = "lfu", // Least Frequently Used
  FIFO = "fifo", // First In, First Out
  TTL = "ttl", // Time To Live
  RANDOM = "random",
}

// Cache configuration
export interface CacheConfig {
  readonly provider: CacheProvider;
  readonly strategy: CacheStrategy;
  readonly eviction_policy: CacheEvictionPolicy;
  readonly default_ttl: number; // in seconds
  readonly max_size: number; // in bytes or items
  readonly compression: boolean;
  readonly serialization: "json" | "msgpack" | "pickle";
  readonly key_prefix: string;
  readonly namespace: string;
}

// Cache key interface
export interface CacheKey {
  readonly namespace: string;
  readonly key: string;
  readonly version?: string;
  readonly tags?: string[];
}

// Cache entry interface
export interface CacheEntry<T = unknown> {
  readonly key: string;
  readonly value: T;
  readonly ttl: number;
  readonly created_at: number;
  readonly accessed_at: number;
  readonly access_count: number;
  readonly size: number;
  readonly tags: string[];
  readonly metadata: Record<string, unknown>;
}

// Cache operation result
export interface CacheOperationResult<T = unknown> {
  readonly success: boolean;
  readonly data?: T;
  readonly hit: boolean;
  readonly ttl?: number;
  readonly error?: string;
  readonly execution_time: number;
}

// Cache statistics
export interface CacheStats {
  readonly hits: number;
  readonly misses: number;
  readonly hit_rate: number;
  readonly total_operations: number;
  readonly total_size: number;
  readonly entry_count: number;
  readonly evictions: number;
  readonly expired_entries: number;
  readonly average_ttl: number;
  readonly memory_usage: number;
}

// Cache provider interface
export interface ICacheProvider {
  readonly get: <T = unknown>(key: string) => Promise<CacheOperationResult<T>>;
  readonly set: <T = unknown>(
    key: string,
    value: T,
    ttl?: number,
    tags?: string[]
  ) => Promise<CacheOperationResult<boolean>>;
  readonly delete: (key: string) => Promise<CacheOperationResult<boolean>>;
  readonly exists: (key: string) => Promise<CacheOperationResult<boolean>>;
  readonly clear: () => Promise<CacheOperationResult<boolean>>;
  readonly get_stats: () => Promise<CacheStats>;
  readonly invalidate_by_tags: (
    tags: string[]
  ) => Promise<CacheOperationResult<number>>;
  readonly get_keys: (
    pattern?: string
  ) => Promise<CacheOperationResult<string[]>>;
}

// Redis cache configuration
export interface RedisCacheConfig extends CacheConfig {
  readonly host: string;
  readonly port: number;
  readonly password?: string;
  readonly database: number;
  readonly cluster: boolean;
  readonly cluster_nodes?: Array<{
    readonly host: string;
    readonly port: number;
  }>;
  readonly connection_pool: {
    readonly min_connections: number;
    readonly max_connections: number;
    readonly idle_timeout: number;
  };
}

// Memory cache configuration
export interface MemoryCacheConfig extends CacheConfig {
  readonly max_memory: number; // in bytes
  readonly cleanup_interval: number; // in seconds
  readonly stats_interval: number; // in seconds
}

// Database cache configuration
export interface DatabaseCacheConfig extends CacheConfig {
  readonly table_name: string;
  readonly connection_string: string;
  readonly cleanup_interval: number;
  readonly index_keys: boolean;
}

// Cache decorator options
export interface CacheDecoratorOptions {
  readonly key?: string | ((args: unknown[]) => string);
  readonly ttl?: number;
  readonly tags?: string[] | ((args: unknown[]) => string[]);
  readonly condition?: (args: unknown[]) => boolean;
  readonly unless?: (result: unknown) => boolean;
  readonly serialize?: boolean;
  readonly compress?: boolean;
}

// Cache invalidation options
export interface CacheInvalidationOptions {
  readonly keys?: string[];
  readonly patterns?: string[];
  readonly tags?: string[];
  readonly namespace?: string;
  readonly cascade?: boolean;
}

// Cache warming configuration
export interface CacheWarmingConfig {
  readonly enabled: boolean;
  readonly strategies: Array<{
    readonly name: string;
    readonly schedule: string; // cron expression
    readonly keys: string[] | (() => Promise<string[]>);
    readonly loader: (key: string) => Promise<unknown>;
    readonly ttl?: number;
  }>;
}

// Cache monitoring configuration
export interface CacheMonitoringConfig {
  readonly enabled: boolean;
  readonly metrics_interval: number; // in seconds
  readonly alert_thresholds: {
    readonly hit_rate_min: number;
    readonly memory_usage_max: number;
    readonly error_rate_max: number;
    readonly response_time_max: number;
  };
  readonly export_metrics: boolean;
  readonly metrics_endpoint?: string;
}

// Cache layer configuration for multi-level caching
export interface CacheLayerConfig {
  readonly name: string;
  readonly provider: CacheProvider;
  readonly config: CacheConfig;
  readonly priority: number;
  readonly read_through: boolean;
  readonly write_through: boolean;
  readonly fallback: boolean;
}

// Multi-level cache configuration
export interface MultiLevelCacheConfig {
  readonly layers: CacheLayerConfig[];
  readonly default_layer: string;
  readonly promotion_policy: "lru" | "lfu" | "manual";
  readonly consistency_mode: "eventual" | "strong";
}

// Cache event types
export enum CacheEventType {
  HIT = "hit",
  MISS = "miss",
  SET = "set",
  DELETE = "delete",
  EVICT = "evict",
  EXPIRE = "expire",
  CLEAR = "clear",
  ERROR = "error",
}

// Cache event
export interface CacheEvent {
  readonly type: CacheEventType;
  readonly key: string;
  readonly namespace: string;
  readonly timestamp: number;
  readonly metadata: Record<string, unknown>;
}

// Cache event listener
export interface CacheEventListener {
  readonly event_types: CacheEventType[];
  readonly handler: (event: CacheEvent) => void | Promise<void>;
}

// Cache serializer interface
export interface ICacheSerializer {
  readonly serialize: (value: unknown) => string | Buffer;
  readonly deserialize: <T = unknown>(data: string | Buffer) => T;
  readonly get_size: (value: unknown) => number;
}

// Cache compressor interface
export interface ICacheCompressor {
  readonly compress: (data: string | Buffer) => Buffer;
  readonly decompress: (data: Buffer) => string | Buffer;
  readonly get_compression_ratio: (
    original: string | Buffer,
    compressed: Buffer
  ) => number;
}

// Cache key generator interface
export interface ICacheKeyGenerator {
  readonly generate: (
    namespace: string,
    key: string,
    version?: string,
    tags?: string[]
  ) => string;
  readonly parse: (generated_key: string) => CacheKey;
  readonly validate: (key: string) => boolean;
}

// Cache metrics collector
export interface CacheMetricsCollector {
  readonly record_hit: (key: string, execution_time: number) => void;
  readonly record_miss: (key: string, execution_time: number) => void;
  readonly record_set: (
    key: string,
    size: number,
    execution_time: number
  ) => void;
  readonly record_delete: (key: string, execution_time: number) => void;
  readonly record_error: (
    key: string,
    error: string,
    execution_time: number
  ) => void;
  readonly get_stats: () => CacheStats;
  readonly reset_stats: () => void;
}

// Cache health check
export interface CacheHealthCheck {
  readonly provider: CacheProvider;
  readonly status: "healthy" | "unhealthy" | "degraded";
  readonly response_time: number;
  readonly error_rate: number;
  readonly memory_usage: number;
  readonly connection_count: number;
  readonly last_check: number;
}

// Cache backup configuration
export interface CacheBackupConfig {
  readonly enabled: boolean;
  readonly schedule: string; // cron expression
  readonly destination: string;
  readonly compression: boolean;
  readonly encryption: boolean;
  readonly retention_days: number;
}

// Cache restore configuration
export interface CacheRestoreConfig {
  readonly source: string;
  readonly overwrite_existing: boolean;
  readonly verify_integrity: boolean;
  readonly batch_size: number;
}

// Distributed cache configuration
export interface DistributedCacheConfig extends CacheConfig {
  readonly nodes: Array<{
    readonly host: string;
    readonly port: number;
    readonly weight: number;
  }>;
  readonly replication_factor: number;
  readonly consistency_level: "one" | "quorum" | "all";
  readonly partition_strategy: "hash" | "range" | "consistent_hash";
  readonly failure_detection: {
    readonly enabled: boolean;
    readonly timeout: number;
    readonly retry_attempts: number;
  };
}
