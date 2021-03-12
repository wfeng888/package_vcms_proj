import logging
import math

from git import RemoteProgress, GitCommandError
from git.repo.base import Repo

from package_vcms import Config, SvnDownloadException, record_log
from package_vcms.utils import format_exc

logger = logging.getLogger(__file__)

class LogGitProgress(RemoteProgress):

    def __init__(self,*args,**kwargs):
        super(LogGitProgress, self).__init__(*args,**kwargs)
        self._last_code = 0
        self._last_count = 0

    code_flags = {
        RemoteProgress.END:'END',
        RemoteProgress.BEGIN:'BEGIN',
        RemoteProgress.COUNTING:'COUNTING',
        RemoteProgress.COMPRESSING:'COMPRESSING',
        RemoteProgress.WRITING:'WRITING',
        RemoteProgress.RECEIVING:'RECEIVING',
        RemoteProgress.RESOLVING:'RESOLVING',
        RemoteProgress.FINDING_SOURCES:'FINDING_SOURCES',
        RemoteProgress.CHECKING_OUT:'CHECKING_OUT'
    }

    def getFlag(self,code):
        _flag = ''
        for i in self.code_flags.keys():
            if self.code_flags.get(i & code,None) :
                _flag += self.code_flags.get(i,None) + '|'
        return _flag or 'Unknown'

    def update(self, op_code, cur_count, max_count=None, message=''):
        if(op_code != self._last_code or cur_count != self._last_count):
            self._last_code = op_code
            self._last_count = cur_count
            logger.info('op=%s, cur_count=%s/max_count=%s, finish=%s, message=%s'% \
                        (self.getFlag(op_code), cur_count,max_count, round(cur_count / (max_count or 100.0),2), message or "NO MESSAGE"))

class Mgit():
    def __init__(self,config:Config):
        self.configs = config
        self.repo = None

    @record_log
    def clone(self):
        logger.info('start to download repo from %s . '%self.configs.repo_url)
        try:
            self.repo = Repo.clone_from(self.configs.repo_url,self.configs.repo_basedir,multi_options=['--depth 1'],progress=LogGitProgress())
        except GitCommandError as e:
            logger.error(format_exc())
            raise SvnDownloadException()
        logger.info('finish to download repo. ')