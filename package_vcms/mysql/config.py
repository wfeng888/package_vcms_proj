from package_vcms import ABSConfig

class MysqlConfigBase(ABSConfig):
    port:int       = 3306
    user:str       = 'root'
    password:str   = 'zxm10@@@'

class MysqlServerConfig(MysqlConfigBase):
    _SECTION = 'mysqld'
    basedir:str
    plugin_dir:str  = '${basedir}/lib/plugin'
    datadir:str     = '${basedir}/data'
    pid_file:str                   = '${basedir}/var/${port}.pid'
    socket:str                     = '${basedir}/var/${port}.socket'
    lc_messages_dir:str            = '${basedir}/share/english'
    character_set_server:str       = 'utf8'
    server_id:int                  = 1
    default_storage_engine:str     = 'INNODB'
    innodb_file_per_table:int      = 1
    innodb_log_buffer_size:str     = '32M'
    innodb_buffer_pool_size:str    = '2G'
    innodb_log_files_in_group:int  = 2
    innodb_thread_concurrency:int  = 32
    innodb_flush_log_at_trx_commit:int = 1
    sync_binlog:int               = 1
    thread_cache_size:int         = 32
    max_connections:int           = 500
    group_concat_max_len:int      = 102400
    event_scheduler:str           = 'off'
    show_compatibility_56:str     = 'on'
    read_only:str                 = 'OFF'
    super_read_only:str           = 'OFF'
    log_bin_trust_function_creators:str = 'ON'


    slow_query_log:str                  = 'ON'
    #
    slow_query_log_file:str         = '${basedir}/log/slow.log'
    long_query_time:int             = 2
    log_slow_slave_statements       = 'ON'
    binlog_format                   = 'ROW'
    expire_logs_days                = 60
    #log_bin                         =${basedir}/log/binlog
    #log_bin_index                   =${basedir}/log/binlog.index
    log_error:str                   = '${basedir}/log/log.err'
    relay_log:str                   = '${basedir}/log/relay_log'
    relay_log_index:str             = '${basedir}/log/relay_log.index'
    general_log_file:str            = '${basedir}/log/general.log'


    master_info_repository:str          = 'TABLE'
    relay_log_info_repository:str       = 'TABLE'
    log_slave_updates:str               = 'OFF'
    gtid_mode:str                       = 'OFF'
    enforce_gtid_consistency:str        = 'OFF'
    max_binlog_size:str                 = '512M'
    innodb_log_file_size:str            = '128M'
    innodb_log_files_in_group:int       = 2
    skip_slave_start:str

    query_cache_size:int                = 0
    key_buffer_size:int                 = 0
    read_buffer_size:str                = '64K'
    read_rnd_buffer_size:str            = '256K'
    sort_buffer_size:str                = '512K'
    bulk_insert_buffer_size:str         = '64M'
    max_allowed_packet:str              = '64M'


    sql_mode:str                        = 'NO_ENGINE_SUBSTITUTION,STRICT_TRANS_TABLES,NO_AUTO_CREATE_USER,ONLY_FULL_GROUP_BY'
    lower_case_table_names:int          =1
    transaction_isolation:str           = 'read_committed'
    autocommit:str                      =1
