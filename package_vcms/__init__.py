import logging
import re
import sys
import traceback
from configparser import ConfigParser
from logging.handlers import TimedRotatingFileHandler
from os import path
from functools import partial, wraps

CURRENT_DIR = path.abspath(path.dirname(__file__))

#打包阶段
STAGE_DOWNLOAD_REPO=1
STAGE_INIT_SEEDDB=2

#日志
#logger = logging.getLogger()
# logging.basicConfig()
filehandler = TimedRotatingFileHandler(path.join(path.split(__file__)[0],'log','running.log'),when='D',backupCount=7,encoding='utf-8')
lformat = logging.Formatter(fmt=' %(asctime)s-%(levelname)s-%(name)s-%(thread)d-%(message)s')
filehandler.setFormatter(lformat)
logging.getLogger().addHandler(filehandler)
logging.getLogger().setLevel(logging.INFO)


#平台
WIN = None
LINUX = None
if sys.platform.startswith('win'):
    WIN = 1
else:
    LINUX = 1

logger = logging.getLogger(__file__)
try:
    import jnius_config
except:
    logger.error("jnius not installed !")
else:
    jnius_config.set_classpath('.', path.join(CURRENT_DIR, 'lib/merge.jar'))

from package_vcms.utils import none_null_stringNone

def substitute_var(iself,value):
    if value and isinstance(value,str):
        _match_obj = None
        _match_obj = re.search(r"(\$\{[^\}]+\})",value,re.IGNORECASE)
        while(_match_obj):
            _src = _match_obj.groups(0)[0]
            m = iself._attributes.get('_'+_src[2:-1],'')
            if not m:
                m = iself.__class__._defaults.get(_src[2:-1])
            value = value.replace(_src,str(m))
            _match_obj = re.search(r"(\$\{[^\}]+\})",value,re.IGNORECASE)
    return value


def getx(cname,iself):
    return substitute_var(iself,iself._attributes.get(cname,None) or iself.__class__._defaults.get(cname[1:]))

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
    return True


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
                    if hasattr(parent,'__dict__') and parent.__dict__.get('_defaults',None):
                        dicts['_defaults'].update(parent.__dict__.get('_defaults'))
                    _addBaseAnnotations(parent.__bases__)
        names = []
        # 将dicts['_attributes']挪到类的__init__()函数进行初始化，是因为如果再这里声明，则dict[_attributes]则为属性为
        # 类的属性，后续就不能使用类的多个instance，因为在任一个instance中改了dict[_attributes]['']的值，则所有instance
        # 获取的值都改变了，因为根据setter和getter方法，所有的instance都获取的是同一个dict[_attributes]['']值。
        # dicts['_attributes'] = dict()
        #加一个_defaults属性，来保存默认值，例如var_name:str = 'var_value'这种，其中的var_value是没法保存起来的。
        # 会被替换为getter/setter函数
        dicts['_defaults'] = dict()
        dicts['_attribute_names'] = set()
        if not dicts.get('__annotations__',None):
            dicts['__annotations__'] = {}
        for name in dicts['__annotations__'].keys():
            if not name.startswith('__') and not name.startswith('_CONS'):
                names.append(name)
        for name in names:
            getter = partial(getx,'_'+name)
            setter = partial(setx,'_'+name)
            dicts['_defaults'][name] = dicts.get(name,None)
            dicts[name] = property(getter,setter)
            dicts['_attribute_names'].add(name)
            dicts['__annotations__']['_'+name] = dicts['__annotations__'][name]
        _addBaseAnnotations(bases)
        return type.__new__(cls,clsname,bases,dicts)

class ABSConfig(object,metaclass=FieldMeta):
    _SECTION='none'
    def __init__(self):
        self._attributes = dict()

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

    def setData(self,cp:ConfigParser):
        if cp:
            _getx = partial(cp.get,self._SECTION)
            # t = _getx('mysql_gz_software_path',fallback=None)
            for i in self._attribute_names:
                if _getx(i,fallback=None):
                    setattr(self,i,_getx(i,fallback=None))

class Config(ABSConfig):
    _SECTION='packaging'
    mysql_gz_software_path:str
    mysql_cnf_path:str    = '${mysql_seed_database_base}/${cnf_name}'
    mysql_software_path:str  = '${mysql_seed_database_base}/bin/mysql'
    mysql_seed_database_base:str
    mysql_packaging_name:str
    mysql_sql_script_base_dir:str
    repo_url:str              = 'git@10.45.156.100:SCMS-IV/DB.git'
    mysql_conn_username:str   = 'root'
    mysql_conn_password:str
    mysql_conn_port:int       = '3306'
    #database_lang=en/zh
    database_lang:str
    work_dir:str
    character_set_server:str  = 'utf8'
    log_level:str
    package_type:str
    stage:int                 = 0
    work_dir_new:str
    download_repo:bool = False
    package_name:str
    package_dir:str
    repo_basedir:str
    cnf_name:str       = 'my.ini' if WIN else 'my.cnf'
    gz_package_path:str

    def __repr__(self):
        res = ''
        for k,v in self._attributes.items():
            res += '%s:%s,'%(k,v)
        return res

    def check(self):
        if  none_null_stringNone(self.mysql_packaging_name) or none_null_stringNone(self.mysql_seed_database_base)\
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


class UnknownFileFormatException(PackageException):
    msg = 'file format is unknown. '

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



class ExceptionHook(object):
    def __init__(self):
        sys.excepthook = self.__HandleException

    def __HandleException(self, excType, excValue, tb):
        try:
            logger.error(exc_info=(excType, excValue, tb))
            logger.error(traceback.format_exception(excType, excValue, tb))

        except:
            pass
        sys.__excepthook__(excType, excValue, tb)


ExceptionHook()