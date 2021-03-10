from package_vcms import FieldMeta
from os import path

class ConfigBase(object,metaclass=FieldMeta):
    host:str
    port:int
    user:str
    password:str

    def __init__(self):
        self._attributes = {}
    def __repr__(self):
        vs = {}
        for k in self._attribute_names:
            if k.find('password') < 0:
                vs[k] = getattr(self,k)
        return vs.__repr__()

    def copy(self,target=None):
        cls = self.__class__
        if not target:
            target = cls()
        for k in self._attribute_names:
            setattr(target,k,getattr(self,k,None))
        return target

    def update(self,source):
        if source:
            for k in (set(self._attribute_names) & set(source._attribute_names)):
                setattr(self,k,getattr(source,k,None))

    def fieldsNotNull(self):
        for k in self._attribute_names:
            if not getattr(self,k,None):
                return False
        return True

    def resetFields(self):
        for k in dir(self.__class__):
            if  not k.startswith('_') and not callable(getattr(self,k)) :
                setattr(self,k,None)

    def check_enum(self,name):
        if hasattr(self,name):
            if hasattr(self,'__'+name):
                return False if getattr(self,name) not in (getattr(self,'__'+name)).get('options') else True
            return True
        return False




class ConfigBase(object,metaclass=FieldMeta):
    port:int
    user:str
    password:str
    host:str

    def __init__(self):
        self._attributes = {}
    def __repr__(self):
        vs = {}
        for k in self._attribute_names:
            if k.find('password') < 0:
                vs[k] = getattr(self,k)
        return vs.__repr__()

    def copy(self,target=None):
        cls = self.__class__
        if not target:
            target = cls()
        for k in self._attribute_names:
            setattr(target,k,getattr(self,k,None))
        return target

    def update(self,source):
        if source:
            for k in (set(self._attribute_names) & set(source._attribute_names)):
                setattr(self,k,getattr(source,k,None))

    def fieldsNotNull(self):
        for k in self._attribute_names:
            if not getattr(self,k,None):
                return False
        return True

    def resetFields(self):
        for k in dir(self.__class__):
            if  not k.startswith('_') and not callable(getattr(self,k)) :
                setattr(self,k,None)

    def check_enum(self,name):
        if hasattr(self,name):
            if hasattr(self,'__'+name):
                return False if getattr(self,name) not in (getattr(self,'__'+name)).get('options') else True
            return True
        return False



class MysqlServerConfig(ConfigBase):
    _SECTION = 'mysqld'
    #D:/database/software/mysql_5.7.33_winx64
    basedir:str
    #${basedir}/lib/plugin
    plugin_dir:str
    #${basedir}/data
    datadir:str
    #${basedir}/var/${port}.pid
    pid_file:str
    #${basedir}/var/${port}.socket
    socket:str
    #${basedir}/share/english
    lc_messages_dir:str
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
    #${basedir}/log/slow.log
    slow_query_log_file:str
    long_query_time:int                 =2
    log_slow_slave_statements       = 'ON'
    binlog_format                   = 'ROW'
    expire_logs_days                = 60
    #log_bin                         =${basedir}/log/binlog
    #log_bin_index                   =${basedir}/log/binlog.index
    #${basedir}/log/log.err
    log_error:str
    #${basedir}/log/relay_log
    relay_log:str
    #${basedir}/log/relay_log.index
    relay_log_index:str
    #${basedir}/log/general.log
    general_log_file:str


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
    autocommit:str                      =0
