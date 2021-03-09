import logging
import os
import subprocess
import sys
from abc import ABCMeta, abstractmethod
import glob

from package_vcms.utils import to_text

logger = logging.getLogger(__file__)
class PlatFormFunc(object,metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def gz(self,target,files=()):
        pass

    @abstractmethod
    def tar(self,target,files=()):
        pass

    @abstractmethod
    def downloadFromSvn(self,url):
        pass

    @abstractmethod
    def portBusy(self,port):
        pass

    def removeFile(self,filelist=()):
        for file in filelist:
            # r_fs = glob.iglob(file,recursive=False)
            logger.debug('remove file %s'%file)
            for r_f in glob.iglob(file,recursive=False):
                logger.debug('remove real file %s'%r_f)
                os.remove(r_f)


class CentOSPlatFormFunc(PlatFormFunc):
    def __init__(self):
        super(CentOSPlatFormFunc, self).__init__()
        self.plat_form='linux'

    def _exec_shell(self,cmd):
        return subprocess.run(cmd,capture_output=True,shell=True,encoding='utf8')

    def gz(self,target,files=()):
        cmd = 'tar -czpf '
        return self.tar(target,files,cmd)

    def tar(self,target,files=(),cmd=None):
        if not cmd:
            cmd = 'tar -cpf '
        cmd += ' ' + target
        if not isinstance(files,(tuple,list)):
            files = (files,)
        for file in files:
            cmd += ' ' + file
        res = self._exec_shell(cmd)
        return res

    def downloadFromSvn(self,url,user,passwd):
        pass

    def portBusy(self,port):
        cmd = 'sudo netstat -apn|grep -v -i grep|grep -w ' + str(port) + '|grep -w LISTEN|wc -l'
        res = self._exec_shell(cmd)
        return int(to_text(res.stdout)) > 0



class WindowsPlatFormFunc(PlatFormFunc):
    def __init__(self):
        super(WindowsPlatFormFunc, self).__init__()
        self.plat_form='windows'

    def gz(self,source,target):
        pass

    def tar(self,source,target):
        pass

    def downloadFromSvn(self,url,user,passwd):
        pass

    def portBusy(self,port):
        pass


if sys.platform.startswith('win'):
    platform_functool = WindowsPlatFormFunc()
else:
    platform_functool = CentOSPlatFormFunc()
