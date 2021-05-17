import logging
import os
import shutil
import stat
from abc import ABCMeta, abstractmethod
from configparser import ConfigParser
from os import path
from shutil import copyfile, copytree, rmtree

from package_vcms import STAGE_DOWNLOAD_REPO, MergeSqlFileException, CURRENT_DIR, MysqlRunningException, \
    IncorrectOSUser, STAGE_INIT_SEEDDB, record_log, WIN, LINUX, ParamException, LOG_BASE
from package_vcms.database_oper import MysqlOper
from package_vcms.git_tools import Mgit
from package_vcms.merge import merge_sql
from package_vcms.mysql.config import MysqlServerConfig
from package_vcms.mysql.constants import MYSQL57_CNF_VAR_PREFERENCE
from package_vcms.platform_func import platform_functool
from package_vcms.utils import getUnArchiveFileName, IsOpen, none_null_stringNone

logger = logging.getLogger(__file__)

class Build(object,metaclass=ABCMeta):

    _PACKAGE_TYPE_DB='DB'
    _PACKAGE_TYPE_SYNC='SYNC'

    def __init__(self,pconfig,pcp):
        self.config = pconfig
        self.cp = pcp

    @abstractmethod
    def buildPackege(self):
        pass

    @abstractmethod
    def buildSyncPackage(self):
        pass

    @record_log
    def build(self):
        if Build._PACKAGE_TYPE_SYNC == self.config.package_type:
            self.buildSyncPackage()
        else:
            self.buildPackege()

    @record_log
    def downloadRepo(self):
        #看看是否要拉取repo代码
        if not (self.config.stage & STAGE_DOWNLOAD_REPO):
            self.config.repo_basedir = path.join(self.config.work_dir_new,'repo')
            # _mgit = Mgit(self.config)
            # _mgit.clone()
            cmd=['git','clone','--depth=1','--no-local','--verbose',self.config.repo_url,self.config.repo_basedir]
            # platform_functool.exec_cmd(cmd)
            logger.info(cmd)
            os.system('git clone --depth=1 --no-local --verbose %s %s'%(self.config.repo_url,self.config.repo_basedir))
            self.config.download_repo = True



class BuildMysql(Build):
    _INSTALL_SCRIPT='install_mysql_57.sh'
    _SYNC_INSTALL_SCRIPT='install.sh'
    _SYNC_CHECK_SCRIPT='check.sh'
    _SYNC_PREDEFINE_SCRIPT='predefine.sh'
    _SYNC_SET_PARAM='set_param.sh'
    def __init__(self,pconfig,pcp):
        super(BuildMysql, self).__init__(pconfig,pcp)
        #self.lang
        # 1 en
        # 0 zh
        self._lang = 1 if self.config.database_lang and self.config.database_lang.lower() == 'en' else 0
        self._startProcess = None
        self._mysqlOper = MysqlOper(pconfig)
        self._sqlScriptsList:list = None
        self._mysqlServerConfig = MysqlServerConfig()

    def checkConfig(self):
        _failure:int = 0
        if none_null_stringNone(self.config.package_name) or none_null_stringNone(self.config.database_lang) \
                or none_null_stringNone(self.config.package_type) or ('zh' != self.config.database_lang  and 'en' != self.config.database_lang ):
            _failure += 1
        if  self.config.stage & 1:
            if none_null_stringNone(self.config.mysql_sql_script_base_dir):
                _failure += 1
        else:
            if none_null_stringNone(self.config.repo_url):
                _failure += 1
        if 'DB' == self.config.package_type:
            if none_null_stringNone(self.config.mysql_conn_username) or none_null_stringNone(self.config.mysql_conn_password) \
                or none_null_stringNone(self.config.mysql_conn_port):
                _failure += 1
            if self.config.stage & 2:
                if none_null_stringNone(self.config.mysql_seed_database_base):
                    _failure += 1
            else:
                if none_null_stringNone(self.config.mysql_gz_software_path):
                    _failure += 1
        elif 'SYNC' == self.config.package_type:
            pass
        else:
            _failure += 1
        if WIN:
            if none_null_stringNone(self.config.mysql_sql_script_base_dir) or 0 == self.config.stage & 1:
                _failure += 1
        if _failure > 0:
            raise ParamException()

    @record_log
    def downloadRepo(self):
        super(BuildMysql, self).downloadRepo()
        if self.config.download_repo:
            self.config.mysql_sql_script_base_dir = path.join(self.config.repo_basedir,'mysql','scimdb_objects')


    @record_log
    def _mergeSql(self):
        if not merge_sql(self.config.mysql_sql_script_base_dir,self._lang,LOG_BASE):
            logger.error('MergeSqlFileException')
            raise MergeSqlFileException()

    @record_log
    def getIdlePort(self):
        for i in range(3308,3400):
            if not IsOpen(i):
                logger.debug('use port%s'%i)
                return i


    @record_log
    def _initDB(self):
        if (not self.config.stage & STAGE_INIT_SEEDDB):
            #将mysql软件gz包解压到work_new目录，并在其中创建data、var、log目录
            shutil.unpack_archive(self.config.mysql_gz_software_path,self.config.work_dir_new)
            assert WIN or LINUX
            _filename = getUnArchiveFileName(self.config.mysql_gz_software_path)
            # if LINUX:
            #     _old_dir = path.join(self.config.work_dir_new,_filename)
            # else:
            #     _old_dir = path.join(self.config.work_dir_new,_filename,_filename)
            self.config.mysql_seed_database_base = path.join(self.config.work_dir_new,self.config.package_name)
            self.config.package_dir = self.config.mysql_seed_database_base
            self.config.work_dir_new = path.dirname(self.config.mysql_seed_database_base)
            os.rename(path.join(self.config.work_dir_new,_filename),self.config.mysql_seed_database_base)
            for i in ('data','var','log'):
                os.mkdir(path.join(self.config.mysql_seed_database_base,i))
            self._mysqlServerConfig.port = self.getIdlePort()
            self.config.mysql_conn_port = self._mysqlServerConfig.port
            logger.debug('self.config.mysql_conn_port=%s, self._mysqlServerConfig.port=%s'%(self.config.mysql_conn_port,self._mysqlServerConfig.port))
            self._mysqlServerConfig.basedir = self.config.mysql_seed_database_base
            self.config.mysql_software_path = path.join(self.config.mysql_seed_database_base,'bin','mysql')
            #生成my.cnf配置文件
            self.makeCnf()
            #初始化数据库 initialize_insecure，修改目录权限，起库，创建用户
            self._mysqlOper.initService()
            _dirname = self.config.mysql_seed_database_base
            if LINUX:
                while(_dirname != os.path.sep):
                    os.chmod(_dirname,stat.S_IRWXO|stat.S_IRWXG|stat.S_IRWXU)
                    _dirname = os.path.dirname(_dirname)
                platform_functool.exec_shell('chown -R mysql:mysql '+ self.config.mysql_seed_database_base)
            _old_pwd = self.config.mysql_conn_password
            self.config.mysql_conn_password = None
            self._mysqlOper.startService()
            self._mysqlOper.waitUntilAlive()
            if not self._mysqlOper.isAlive():
                logger.error('mysql not running and start failed, abort it! ')
                raise MysqlRunningException()
            self._mysqlOper.execSql(sql='create user root identified by \'%s\' ; grant all on *.* to root ; alter user root@\'localhost\' identified by \'%s\' ; flush privileges ;'%(_old_pwd,_old_pwd))
            self.config.mysql_conn_password = _old_pwd

    @record_log
    def _getSQLScripts(self):
        self._sqlScriptsList = ['init_db.sql', \
                                path.join('tables','table_shell_merge_mysql.sql'), \
                                path.join('views','views_shell_merge_mysql.sql') , \
                                path.join('triggers','triggers_shell_merge_mysql.sql'), \
                                path.join('procedure','procedures_functions_shell_merge_mysql.sql') \
                                ]
        if self._lang == 1:
            self._sqlScriptsList.append(path.join('db_basic_data_en','basic_data_shell_merge_mysql.sql'))
        else:
            self._sqlScriptsList.append(path.join('db_basic_data','basic_data_shell_merge_mysql.sql'))

    @record_log
    def _prepare(self):
        self.checkConfig()
        os.chdir(self.config.work_dir_new)
        #windows现在不能解决jnius运行失败的问题，所以不能进行脚本合并。
        self.downloadRepo()
        if LINUX:
            self._mergeSql()
        self._getSQLScripts()

    @record_log
    def buildSyncPackage(self):
        logger.info('buil')
        self._prepare()
        os.mkdir(self.config.package_dir)
        for i in self._sqlScriptsList:
            copyfile(path.join(self.config.mysql_sql_script_base_dir,i),path.join(self.config.package_dir,path.basename(i)))
        #生成一个安装配置文件,这个给shell脚本使用
        with open(path.join(self.config.package_dir,'config.param'),'xt',encoding='utf8') as f:
            for i in ('mysql_sync_ip=','mysql_sync_port=','mysql_user=','mysql_passwd=','mysql_software_base=','ignore_error=Y','mysql_socket='):
                f.write(i+'\n')
            f.flush()
        #生成一个安装配置文件,这个给python脚本使用
        with open(path.join(self.config.package_dir,'config.ini'),'xt',encoding='utf8') as f:
            for i in ('[install]','mysql_sync_ip=','mysql_sync_port=','mysql_user=','mysql_passwd=','mysql_software_base=','ignore_error=Y','mysql_socket='):
                f.write(i+'\n')
            f.flush()
        #将shell安装脚本copy到安装包中
        for i in os.listdir(os.path.join(CURRENT_DIR,'resource')) :
            if i.endswith('.sh'):
                copyfile(path.join(CURRENT_DIR,'resource',i),path.join(self.config.package_dir,i))
        if self.config.download_repo:
            rmtree(self.config.repo_basedir)
        #直接打一个gz包
        logger.debug('package %s'% self.config.package_name+'.tar.gz')
        self.config.gz_package_path = platform_functool.gz(self.config.package_dir,path.dirname(self.config.package_dir))
        #工作目录中的打包文件不用了，删掉
        logger.debug('remove %s'%self.config.package_name)
        rmtree(self.config.package_dir)

    @record_log
    def _checkSeedCorrect(self):
        return self._mysqlOper.getVar('datadir').replace('\\','').startswith(path.join(self.config.mysql_seed_database_base,'data').replace('\\',''))


    @record_log
    def _installSql(self):
        for file in self._sqlScriptsList:
            logger.info('execute %s'%file)
            res = self._mysqlOper.execSql(sqlfile=path.join(self.config.mysql_sql_script_base_dir,file),dbname= None if file == 'init_db.sql' else 'usmsc' )
            if getattr(res,'stderr'):
                logger.error(res.stderr)


    @record_log
    def buildPackege(self):
        self._prepare()
        self._initDB()
        if self._mysqlOper.isShutdown():
            # 如果mysql进程没有运行，这里尝试启动一下
            logger.error('mysql not running , start')
            self._startProcess = self._mysqlOper.startService()
            self._mysqlOper.waitUntilAlive()
            if not self._mysqlOper.isAlive():
                logger.error('mysql not running and start failed, abort it! ')
                raise MysqlRunningException()
        #检查一下运行中的mysql进程是否与配置的打包目录一致
        if not self._checkSeedCorrect():
            logger.error('current active mysqld process is not the seed database. abort! ')
            raise IncorrectOSUser()
        logger.info('drop exists database. ')
        self._mysqlOper.execSql(sql='drop database if exists usmsc;drop database if exists usmschis;drop database if exists activiti;')
        logger.info('install scripts. ')
        self._installSql()
        logger.info('stop mysql process. ')
        self._mysqlOper.stopService()
        #如果自动下载git代码的话，需要把下载后的repo删掉
        logger.info('remove repo file. ')
        if self.config.download_repo:
            rmtree(self.config.repo_basedir)
        logger.info('copy packaing file. ')
        if  self.config.stage & STAGE_INIT_SEEDDB :
            copytree(self.config.mysql_seed_database_base,self.config.package_dir,symlinks=True)
        # 删除log目录下，除log.err之外的其它日志文件
        logger.debug(path.join(self.config.package_dir,'log','*'))
        _logdir = path.join(self.config.package_dir,'log')
        logger.debug('logdir= %s'%_logdir)
        _dellist = [path.join(_logdir,i) for i in os.listdir(_logdir) if '.err' != path.splitext(i)[1]]
        # 删除data目录下的redo日志文件，节省打包空间
        _datadir = path.join(self.config.package_dir,'data')
        _dellist.append(path.join(_datadir,'ib_logfile*'))
        #真正删除的地方
        platform_functool.removeFile(filelist=_dellist)
        # #切换到打包目录
        # os.chdir(self.config.work_dir_new)
        logger.info('start packaging. ')
        if LINUX:
            #先打一个tar包
            logger.debug('package %s'% self.config.package_dir+'.tar')
            platform_functool.tar(self.config.package_dir,ar_root=path.dirname(self.config.package_dir))
            rmtree(self.config.package_dir)
            copyfile(path.join(CURRENT_DIR,'resource',BuildMysql._INSTALL_SCRIPT),path.join(self.config.work_dir_new,BuildMysql._INSTALL_SCRIPT))
            #再打一个gz包，别问为什么package_type，安装脚本里面写死了要处理的是tar包，不是gz包
            logger.debug('package %s'% self.config.package_name+'.tar.gz')
            self.config.gz_package_path = platform_functool.gz(self.config.package_dir,ar_root=self.config.work_dir_new)
            #tar包用完了，删掉
            logger.debug('remove %s'%self.config.package_name+'.tar')
            os.remove(self.config.package_name+'.tar')
            #shell也不要了
            os.remove(BuildMysql._INSTALL_SCRIPT)
        else:
            for i in os.listdir(os.path.join(CURRENT_DIR,'resource')) :
                if i.endswith('.bat'):
                    copyfile(path.join(CURRENT_DIR,'resource',i),path.join(self.config.package_dir,i))
            self.config.gz_package_path = platform_functool.gz(self.config.package_dir)
            rmtree(self.config.package_dir)
        logger.info('finish packaging. ')
        logger.info('purge garbage. ')


    @record_log
    def makeCnf(self):
        cnf = ConfigParser(allow_no_value=True)
        _ov = None
        _ov = None
        cnf.add_section(self._mysqlServerConfig._SECTION)
        for option in MYSQL57_CNF_VAR_PREFERENCE[self._mysqlServerConfig._SECTION]:
            if isinstance(option,(list,tuple)) :
                _op = (option[1] or option[0]).replace('-','_')
            else:
                _op = option.replace('-','_')
            _ov = getattr(self._mysqlServerConfig,_op,None)
            if _ov:
                cnf.set(self._mysqlServerConfig._SECTION,_op,str(_ov))

        self.config.mysql_cnf_path = path.join(self.config.mysql_seed_database_base,self.config.cnf_name)
        with open(self.config.mysql_cnf_path,'x',encoding='utf-8') as wf:
            cnf.write(wf)
        assert path.exists(self.config.mysql_cnf_path)
