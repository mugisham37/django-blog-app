/**
 * Database-related type definitions
 */

// Database provider types
export enum DatabaseProvider {
  POSTGRESQL = "postgresql",
  MYSQL = "mysql",
  SQLITE = "sqlite",
  MONGODB = "mongodb",
  REDIS = "redis",
}

// Connection pool configuration
export interface ConnectionPoolConfig {
  readonly min_connections: number;
  readonly max_connections: number;
  readonly idle_timeout: number; // in seconds
  readonly connection_timeout: number; // in seconds
  readonly validation_query: string;
  readonly test_on_borrow: boolean;
  readonly test_on_return: boolean;
  readonly test_while_idle: boolean;
}

// Database connection configuration
export interface DatabaseConfig {
  readonly provider: DatabaseProvider;
  readonly host: string;
  readonly port: number;
  readonly database: string;
  readonly username: string;
  readonly password: string;
  readonly ssl: boolean;
  readonly pool: ConnectionPoolConfig;
  readonly read_replicas?: Array<{
    readonly host: string;
    readonly port: number;
    readonly weight: number;
  }>;
  readonly options: Record<string, unknown>;
}

// Query result interface
export interface QueryResult<T = unknown> {
  readonly rows: T[];
  readonly row_count: number;
  readonly affected_rows: number;
  readonly execution_time: number;
  readonly query: string;
  readonly parameters: unknown[];
}

// Transaction interface
export interface ITransaction {
  readonly id: string;
  readonly start_time: number;
  readonly isolation_level: IsolationLevel;
  readonly readonly: boolean;
  readonly commit: () => Promise<void>;
  readonly rollback: () => Promise<void>;
  readonly savepoint: (name: string) => Promise<void>;
  readonly rollback_to_savepoint: (name: string) => Promise<void>;
}

// Isolation levels
export enum IsolationLevel {
  READ_UNCOMMITTED = "read_uncommitted",
  READ_COMMITTED = "read_committed",
  REPEATABLE_READ = "repeatable_read",
  SERIALIZABLE = "serializable",
}

// Repository interface
export interface IRepository<T, ID = number> {
  readonly find_by_id: (id: ID) => Promise<T | null>;
  readonly find_all: (options?: FindOptions) => Promise<T[]>;
  readonly find_one: (criteria: Partial<T>) => Promise<T | null>;
  readonly find_many: (
    criteria: Partial<T>,
    options?: FindOptions
  ) => Promise<T[]>;
  readonly create: (
    entity: Omit<T, "id" | "created_at" | "updated_at">
  ) => Promise<T>;
  readonly update: (id: ID, updates: Partial<T>) => Promise<T | null>;
  readonly delete: (id: ID) => Promise<boolean>;
  readonly count: (criteria?: Partial<T>) => Promise<number>;
  readonly exists: (criteria: Partial<T>) => Promise<boolean>;
}

// Find options
export interface FindOptions {
  readonly limit?: number;
  readonly offset?: number;
  readonly order_by?: Array<{
    readonly field: string;
    readonly direction: "ASC" | "DESC";
  }>;
  readonly include?: string[];
  readonly select?: string[];
}

// Query builder interface
export interface IQueryBuilder {
  readonly select: (fields?: string[]) => IQueryBuilder;
  readonly from: (table: string) => IQueryBuilder;
  readonly where: (condition: string, parameters?: unknown[]) => IQueryBuilder;
  readonly and_where: (
    condition: string,
    parameters?: unknown[]
  ) => IQueryBuilder;
  readonly or_where: (
    condition: string,
    parameters?: unknown[]
  ) => IQueryBuilder;
  readonly join: (table: string, condition: string) => IQueryBuilder;
  readonly left_join: (table: string, condition: string) => IQueryBuilder;
  readonly right_join: (table: string, condition: string) => IQueryBuilder;
  readonly inner_join: (table: string, condition: string) => IQueryBuilder;
  readonly group_by: (fields: string[]) => IQueryBuilder;
  readonly having: (condition: string, parameters?: unknown[]) => IQueryBuilder;
  readonly order_by: (
    field: string,
    direction?: "ASC" | "DESC"
  ) => IQueryBuilder;
  readonly limit: (count: number) => IQueryBuilder;
  readonly offset: (count: number) => IQueryBuilder;
  readonly build: () => { query: string; parameters: unknown[] };
  readonly execute: <T = unknown>() => Promise<QueryResult<T>>;
}

// Migration interface
export interface IMigration {
  readonly version: string;
  readonly name: string;
  readonly up: (connection: IDatabaseConnection) => Promise<void>;
  readonly down: (connection: IDatabaseConnection) => Promise<void>;
}

// Migration status
export interface MigrationStatus {
  readonly version: string;
  readonly name: string;
  readonly applied_at?: string;
  readonly execution_time?: number;
  readonly status: "pending" | "applied" | "failed";
  readonly error?: string;
}

// Database connection interface
export interface IDatabaseConnection {
  readonly query: <T = unknown>(
    sql: string,
    parameters?: unknown[]
  ) => Promise<QueryResult<T>>;
  readonly execute: (
    sql: string,
    parameters?: unknown[]
  ) => Promise<QueryResult>;
  readonly begin_transaction: (
    isolation_level?: IsolationLevel
  ) => Promise<ITransaction>;
  readonly close: () => Promise<void>;
  readonly is_connected: () => boolean;
  readonly get_stats: () => ConnectionStats;
}

// Connection statistics
export interface ConnectionStats {
  readonly active_connections: number;
  readonly idle_connections: number;
  readonly total_connections: number;
  readonly queries_executed: number;
  readonly average_query_time: number;
  readonly errors_count: number;
  readonly uptime: number;
}

// Database schema definition
export interface TableSchema {
  readonly name: string;
  readonly columns: ColumnDefinition[];
  readonly indexes: IndexDefinition[];
  readonly constraints: ConstraintDefinition[];
  readonly triggers?: TriggerDefinition[];
}

// Column definition
export interface ColumnDefinition {
  readonly name: string;
  readonly type: string;
  readonly nullable: boolean;
  readonly default_value?: unknown;
  readonly auto_increment: boolean;
  readonly primary_key: boolean;
  readonly unique: boolean;
  readonly foreign_key?: {
    readonly table: string;
    readonly column: string;
    readonly on_delete: "CASCADE" | "SET NULL" | "RESTRICT";
    readonly on_update: "CASCADE" | "SET NULL" | "RESTRICT";
  };
}

// Index definition
export interface IndexDefinition {
  readonly name: string;
  readonly columns: string[];
  readonly unique: boolean;
  readonly type: "btree" | "hash" | "gin" | "gist";
  readonly where?: string;
}

// Constraint definition
export interface ConstraintDefinition {
  readonly name: string;
  readonly type: "primary_key" | "foreign_key" | "unique" | "check";
  readonly columns: string[];
  readonly reference?: {
    readonly table: string;
    readonly columns: string[];
  };
  readonly check_expression?: string;
}

// Trigger definition
export interface TriggerDefinition {
  readonly name: string;
  readonly event: "INSERT" | "UPDATE" | "DELETE";
  readonly timing: "BEFORE" | "AFTER" | "INSTEAD OF";
  readonly function_name: string;
  readonly condition?: string;
}

// Seed data interface
export interface SeedData {
  readonly table: string;
  readonly data: Record<string, unknown>[];
  readonly truncate_before: boolean;
  readonly update_on_conflict: boolean;
  readonly conflict_columns?: string[];
}

// Database backup configuration
export interface BackupConfig {
  readonly enabled: boolean;
  readonly schedule: string; // cron expression
  readonly destination: string;
  readonly compression: boolean;
  readonly encryption: boolean;
  readonly retention_days: number;
  readonly include_tables?: string[];
  readonly exclude_tables?: string[];
}

// Database monitoring metrics
export interface DatabaseMetrics {
  readonly connections: {
    readonly active: number;
    readonly idle: number;
    readonly total: number;
    readonly max_used: number;
  };
  readonly queries: {
    readonly total: number;
    readonly per_second: number;
    readonly average_duration: number;
    readonly slow_queries: number;
  };
  readonly performance: {
    readonly cpu_usage: number;
    readonly memory_usage: number;
    readonly disk_usage: number;
    readonly cache_hit_ratio: number;
  };
  readonly replication: {
    readonly lag: number;
    readonly status: "healthy" | "lagging" | "broken";
    readonly replicas_count: number;
  };
}

// Query performance statistics
export interface QueryPerformanceStats {
  readonly query_hash: string;
  readonly query_template: string;
  readonly execution_count: number;
  readonly total_time: number;
  readonly average_time: number;
  readonly min_time: number;
  readonly max_time: number;
  readonly rows_examined: number;
  readonly rows_sent: number;
  readonly last_executed: string;
}

// Database health check
export interface DatabaseHealthCheck {
  readonly status: "healthy" | "unhealthy" | "degraded";
  readonly response_time: number;
  readonly connection_status: boolean;
  readonly replication_status: boolean;
  readonly disk_space: {
    readonly total: number;
    readonly used: number;
    readonly available: number;
    readonly usage_percentage: number;
  };
  readonly last_backup: string;
  readonly errors: string[];
}

// Bulk operation configuration
export interface BulkOperationConfig {
  readonly batch_size: number;
  readonly parallel_batches: number;
  readonly continue_on_error: boolean;
  readonly progress_callback?: (processed: number, total: number) => void;
}

// Bulk insert result
export interface BulkInsertResult {
  readonly inserted_count: number;
  readonly failed_count: number;
  readonly errors: Array<{
    readonly row_index: number;
    readonly error: string;
  }>;
  readonly execution_time: number;
}

// Database event types
export enum DatabaseEventType {
  CONNECTION_OPENED = "connection_opened",
  CONNECTION_CLOSED = "connection_closed",
  QUERY_EXECUTED = "query_executed",
  TRANSACTION_STARTED = "transaction_started",
  TRANSACTION_COMMITTED = "transaction_committed",
  TRANSACTION_ROLLED_BACK = "transaction_rolled_back",
  MIGRATION_APPLIED = "migration_applied",
  BACKUP_COMPLETED = "backup_completed",
  ERROR_OCCURRED = "error_occurred",
}

// Database event
export interface DatabaseEvent {
  readonly type: DatabaseEventType;
  readonly timestamp: number;
  readonly connection_id?: string;
  readonly query?: string;
  readonly execution_time?: number;
  readonly error?: string;
  readonly metadata: Record<string, unknown>;
}

// Database event listener
export interface DatabaseEventListener {
  readonly event_types: DatabaseEventType[];
  readonly handler: (event: DatabaseEvent) => void | Promise<void>;
}

// Read/Write splitting configuration
export interface ReadWriteSplitConfig {
  readonly enabled: boolean;
  readonly read_replicas: Array<{
    readonly host: string;
    readonly port: number;
    readonly weight: number;
  }>;
  readonly load_balancing: "round_robin" | "weighted" | "least_connections";
  readonly failover: {
    readonly enabled: boolean;
    readonly timeout: number;
    readonly retry_attempts: number;
  };
}

// Sharding configuration
export interface ShardingConfig {
  readonly enabled: boolean;
  readonly strategy: "hash" | "range" | "directory";
  readonly shards: Array<{
    readonly name: string;
    readonly connection: DatabaseConfig;
    readonly range?: {
      readonly start: unknown;
      readonly end: unknown;
    };
  }>;
  readonly shard_key: string;
}
