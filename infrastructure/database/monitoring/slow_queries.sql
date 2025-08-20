-- Slow Query Analysis and Monitoring Queries
-- These queries help identify performance bottlenecks and optimization opportunities

-- 1. Top 20 slowest queries by average execution time
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    min_time,
    max_time,
    stddev_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 20;

-- 2. Queries with highest total execution time
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    (total_time / sum(total_time) OVER()) * 100 AS percentage_of_total
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 20;

-- 3. Most frequently executed queries
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    (calls / sum(calls) OVER()) * 100 AS percentage_of_calls
FROM pg_stat_statements 
ORDER BY calls DESC 
LIMIT 20;

-- 4. Queries with low cache hit ratio (potential I/O bottlenecks)
SELECT 
    query,
    calls,
    total_time,
    shared_blks_hit,
    shared_blks_read,
    shared_blks_hit + shared_blks_read as total_blks,
    CASE 
        WHEN shared_blks_hit + shared_blks_read = 0 THEN 0
        ELSE 100.0 * shared_blks_hit / (shared_blks_hit + shared_blks_read)
    END AS hit_percent
FROM pg_stat_statements 
WHERE shared_blks_hit + shared_blks_read > 0
ORDER BY hit_percent ASC, total_time DESC
LIMIT 20;

-- 5. Current running queries (potential locks and long-running operations)
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state,
    wait_event_type,
    wait_event
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
    AND state != 'idle'
ORDER BY duration DESC;

-- 6. Table statistics and usage patterns
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables 
ORDER BY seq_scan DESC;

-- 7. Index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

-- 8. Unused or rarely used indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes 
WHERE idx_scan < 10
ORDER BY pg_relation_size(indexrelid) DESC;

-- 9. Database size and growth tracking
SELECT 
    datname,
    pg_size_pretty(pg_database_size(datname)) AS size,
    pg_database_size(datname) AS size_bytes
FROM pg_database 
WHERE datname NOT IN ('template0', 'template1', 'postgres')
ORDER BY pg_database_size(datname) DESC;

-- 10. Table sizes and bloat estimation
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size,
    n_live_tup,
    n_dead_tup,
    CASE 
        WHEN n_live_tup > 0 
        THEN round((n_dead_tup::float / n_live_tup::float) * 100, 2)
        ELSE 0 
    END AS dead_tuple_percent
FROM pg_stat_user_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 11. Lock monitoring
SELECT 
    l.mode,
    l.locktype,
    l.database,
    l.relation,
    l.page,
    l.tuple,
    l.classid,
    l.granted,
    a.query,
    a.query_start,
    age(now(), a.query_start) AS query_age,
    a.pid
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT l.granted
ORDER BY a.query_start;

-- 12. Connection statistics
SELECT 
    state,
    count(*) as connections,
    max(now() - query_start) as max_duration,
    avg(now() - query_start) as avg_duration
FROM pg_stat_activity 
WHERE pid != pg_backend_pid()
GROUP BY state
ORDER BY connections DESC;