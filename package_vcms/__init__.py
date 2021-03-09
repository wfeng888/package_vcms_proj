import logging
import sys
from configparser import ConfigParser
from logging.handlers import TimedRotatingFileHandler
from os import path
from functools import partial, wraps

CURRENT_DIR = path.abspath(path.dirname(__file__))
logger = logging.getLogger()
# logging.basicConfig()
filehandler = TimedRotatingFileHandler(path.join(path.split(__file__)[0],'running.log'),when='D',backupCount=7,encoding='utf-8')
lformat = logging.Formatter(fmt=' %(asctime)s-%(levelname)s-%(name)s-%(thread)d-%(message)s')
filehandler.setFormatter(lformat)
logger.addHandler(filehandler)
logger.setLevel(logging.INFO)

logger = logging.getLogger(__file__)

WIN = None
LINUX = None
if sys.platform.startswith('win'):
    WIN = 1
else:
    LINUX = 1


try:
    import jnius_config
except:
    logger.error("jnius not installed !")
else:
    jnius_config.set_classpath('.', path.join(CURRENT_DIR,'merge.jar'))

from package_vcms.utils import none_null_stringNone

def getx(cname,iself):
    return iself._attributes.get(cname,None)

def setx(cname,cself, value):
    cls = cself.__class__.__annotations__[cname]
    if value == None:
        cself._attributes[cname] = None
        return
    if isinstance(cls,int) or cls == int:
        if not none_null_stringNone(value):
            cself._attributes[cname] = int(value)
    elif isinstance(cls,(list,tuple)) or cls in (list,tuple):
        if not isinstance(value,(list,tuple)):
            cself._attributes[cname] = value.split(',')
        else:
            cself._attributes[cname] = value
    elif isinstance(cls,dict) or cls == dict:
        if not isinstance(value,dict):
            tmplist = value.split(',')
            cself._attributes[cname][tmplist.split(':')[0]] = tmplist.split(':')[1]
        else:
            cself._attributes[cname] = value
    elif isinstance(cls,bool) or cls == bool:
        cself._attributes[cname] = True if value and str(value).upper() == 'TRUE' else False
    else:
        cself._attributes[cname] = value


class FieldMeta(type):
    def __new__(cls,clsname,bases,dicts):
        def _addBaseAnnotations(parents):
            for parent in parents:
                if not parent.__name__ == 'object' and not parent.__name__ == 'type':
                    if hasattr(parent,'__dict__') and parent.__dict__.get('__annotations__',None):
                        for key in  (set(parent.__dict__['__annotations__'].keys()) - set(dicts['__annotations__'].keys())):
                            dicts['__annotations__'][key] = parent.__dict__['__annotations__'][key]
                    if hasattr(parent,'__dict__') and parent.__dict__.get('_attribute_names',None):
                        dicts['_attribute_names'].update(parent.__dict__.get('_attribute_names'))
                    _addBaseAnnotations(parent.__bases__)
        names = []
        # dicts['_attributes'] = dict()
        dicts['_attribute_names'] = set()
        if not dicts.get('__annotations__',None):
            dicts['__annotations__'] = {}
        for name in dicts['__annotations__'].keys():
            if not name.startswith('__') and not name.startswith('_CONS'):
                names.append(name)
        for name in names:
            getter = partial(getx,'_'+name)
            setter = partial(setx,'_'+name)
            dicts[name] = property(getter,setter)
            dicts['_attribute_names'].add(name)
            dicts['__annotations__']['_'+name] = dicts['__annotations__'][name]
        _addBaseAnnotations(bases)
        return type.__new__(cls,clsname,bases,dicts)

class Config(metaclass=FieldMeta):
    _SECTION='packaging'
    _PACKAGE_TYPE_DB='DB'
    _PACKAGE_TYPE_SYNC='SYNC'
    _INSTALL_SCRIPT='resource/install_mysql_57.sh'
    _SYNC_INSTALL_SCRIPT='resource/install.sh'
    _SYNC_CHECK_SCRIPT='resource/check.sh'
    _SYNC_PREDEFINE_SCRIPT='resource/predefine.sh'
    _SYNC_SET_PARAM='resource/set_param.sh'
    mysql_gz_software_path:str
    mysql_cnf_path:str
    mysql_software_path:str
    mysql_seed_database_base:str
    mysql_install_shell:str
    mysql_packaging_name:str
    mysql_sql_script_base_dir:str
    repo_url:str
    mysql_conn_username:str
    mysql_conn_password:str
    mysql_conn_port:int
    #database_lang=en/zh
    database_lang:str
    work_dir:str
    character_set_server:str
    log_level:str
    package_type:str
    stage:int
    work_dir_new:str
    download_repo:bool = False
    package_name:str

    def __init__(self):
        self._attributes = dict()

    def __repr__(self):
        res = ''
        for k,v in self._attributes.items():
            res += '%s:%s,'%(k,v)
        return res

    def setData(self,cp:ConfigParser):
        if cp:
            _getx = partial(cp.get,self._SECTION)
            # t = _getx('mysql_gz_software_path',fallback=None)
            for i in self._attribute_names:
                setattr(self,i,_getx(i,fallback=None))
            # self.mysql_gz_software_path = cp.get(self._SECTION,'mysql_gz_software_path',fallback=None)
            # self.mysql_cnf_path = cp.get(self._SECTION,'mysql_cnf_path',fallback=None)
            # self.mysql_seed_database_base = cp.get(self._SECTION,'mysql_seed_database_base',fallback=None)
            # self.mysql_install_shell = cp.get(self._SECTION,'mysql_install_shell',fallback=None)
            # self.mysql_packaging_name = cp.get(self._SECTION,'mysql_packaging_name',fallback=None)
            # self.mysql_sql_script_base_dir = cp.get(self._SECTION,'mysql_sql_script_base_dir',fallback=None)
            # self.svn_user = cp.get(self._SECTION,'svn_user',fallback=None)
            # self.svn_password = cp.get(self._SECTION,'svn_password',fallback=None)
            # self.svn_url = cp.get(self._SECTION,'svn_url',fallback=None)
            # self.mysql_conn_username = cp.get(self._SECTION,'mysql_conn_username',fallback=None)
            # self.mysql_conn_password = cp.get(self._SECTION,'mysql_conn_password',fallback=None)
            # self.mysql_conn_port = cp.get(self._SECTION,'mysql_conn_port',fallback=None)
            # self.database_lang = cp.get(self._SECTION,'database_lang',fallback=None)
            # self.character_set_server = cp.get(self._SECTION,'character_set_server',fallback=None)
            # self.mysql_software_path = cp.get(self._SECTION,'mysql_software_path',fallback=None)
            # self.work_dir = cp.get(self._SECTION,'work_dir',fallback=None)

    def check(self):
        if none_null_stringNone(self.mysql_install_shell) or none_null_stringNone(self.mysql_packaging_name) or none_null_stringNone(self.mysql_seed_database_base)\
            or none_null_stringNone(self.mysql_conn_port) or none_null_stringNone(self.mysql_sql_script_base_dir) or none_null_stringNone(self.mysql_conn_password)\
            or none_null_stringNone(self.mysql_conn_username) or none_null_stringNone(self.mysql_software_path) :
            return False
        return True

class PackageException(Exception):
    msg = 'PackageException '
    def __repr__(self):
        return self.msg

    def __init__(self,msg=None):
        if msg:
            self.msg += msg
        Exception.__init__(self,self.msg)

class SvnDownloadException(PackageException):
    msg = 'SvnDownloadException '


class MergeSqlFileException(PackageException):
    msg = 'MergeSqlFileException '

class ConfigFileException(PackageException):
    msg = 'ConfigFileException . not all config item setted. '

class IncorrectOSUser(PackageException):
    msg = 'Os user must be mysql or root. The current user is '


class IncorrectOSUser(PackageException):
    msg = 'current active mysqld process is not the seed database. '


class MysqlRunningException(PackageException):
    msg = 'mysql not running and start failed. '


def record_log(func):
    @wraps(func)
    def  wrapper(*args,**kwargs):
        logger.debug('begin')
        logger.debug('call function %s.%s  params: args:%s,kwargs:%s'
                  % (func.__qualname__,func.__name__,args,kwargs) )
        r = func(*args,**kwargs)
        logger.debug('type(r):%s,r.__class__:%s' % (type(r),r.__class__) )
        logger.debug('the end')
        return r
    return wrapper