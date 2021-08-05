import logging
import os

from package_vcms import record_log, LINUX, CURRENT_DIR, none_null_stringNone
from package_vcms.platform_func import platform_functool

logger =  logging.getLogger(__file__)
if LINUX:
    try:
        from jnius import autoclass
    except:
        logger.error("jnius not installed !")

@record_log
def merge_sql(sqlbase,lang,log_base):
    logger.info('start merging sql scripts. ')
    if LINUX:
        MergeTest = autoclass('com.znv.vcms.merge.MergeTest')
        merget = MergeTest()
        ret = merget.mergeTest(sqlbase,lang,log_base)
        ret = int(ret)
    else:
        ret = platform_functool.exec_shell("java -jar "+os.path.join(CURRENT_DIR,"lib","merge.jar") + " " + sqlbase + " " \
                                     + str(lang) + " " + log_base, stdout=True)
        ret = 0 if  "0" == ret else 1
    return True if ret==0 else False
