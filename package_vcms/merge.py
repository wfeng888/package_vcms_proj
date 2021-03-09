import logging
import os

from package_vcms import record_log

logger =  logging.getLogger(__file__)
try:
    from jnius import autoclass
except:
    logger.error("jnius not installed !")

@record_log
def merge_sql(sqlbase,lang):
    MergeTest = autoclass('com.znv.vcms.merge.MergeTest')
    merget = MergeTest()
    ret = merget.mergeTest(sqlbase,lang)
    ret = int(ret)
    return True if ret==0 else False
