import logging
from os import path
import sys
import time
import traceback
import types
import codecs
import socket

from package_vcms import WIN

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):

            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X




try:
    codecs.lookup_error('surrogateescape')
    HAS_SURROGATEESCAPE = True
except LookupError:
    HAS_SURROGATEESCAPE = False


_COMPOSED_ERROR_HANDLERS = frozenset((None, 'surrogate_or_replace',
                                      'surrogate_or_strict',
                                      'surrogate_then_replace'))


class  ContextManager(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close()


def to_bytes(obj, encoding='utf-8', errors=None, nonstring='simplerepr'):
    """Make sure that a string is a byte string

    :arg obj: An object to make sure is a byte string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a text string to
        a byte string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the text string is not
        encodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/2/library/codecs.html#codec-base-classes>`_
        may be specified. There are three additional error strategies
        specifically aimed at helping people to port code.  The first two are:

            :surrogate_or_strict: Will use ``surrogateescape`` if it is a valid
                handler, otherwise it will use ``strict``
            :surrogate_or_replace: Will use ``surrogateescape`` if it is a valid
                handler, otherwise it will use ``replace``.

        Because ``surrogateescape`` was added in Python3 this usually means that
        Python3 will use ``surrogateescape`` and Python2 will use the fallback
        error handler. Note that the code checks for ``surrogateescape`` when the
        module is imported.  If you have a backport of ``surrogateescape`` for
        Python2, be sure to register the error handler prior to importing this
        module.

        The last error handler is:

            :surrogate_then_replace: Will use ``surrogateescape`` if it is a valid
                handler.  If encoding with ``surrogateescape`` would traceback,
                surrogates are first replaced with a replacement characters
                and then the string is encoded using ``replace`` (which replaces
                the rest of the nonencodable bytes).  If ``surrogateescape`` is
                not present it will simply use ``replace``.  (Added in Ansible 2.3)
                This strategy is designed to never traceback when it attempts
                to encode a string.

        The default until Ansible-2.2 was ``surrogate_or_replace``
        From Ansible-2.3 onwards, the default is ``surrogate_then_replace``.

    :kwarg nonstring: The strategy to use if a nonstring is specified in
        ``obj``.  Default is 'simplerepr'.  Valid values are:

        :simplerepr: The default.  This takes the ``str`` of the object and
            then returns the bytes version of that string.
        :empty: Return an empty byte string
        :passthru: Return the object passed in
        :strict: Raise a :exc:`TypeError`

    :returns: Typically this returns a byte string.  If a nonstring object is
        passed in this may be a different type depending on the strategy
        specified by nonstring.  This will never return a text string.

    .. note:: If passed a byte string, this function does not check that the
        string is valid in the specified encoding.  If it's important that the
        byte string is in the specified encoding do::

            encoded_string = to_bytes(to_text(input_string, 'latin-1'), 'utf-8')

    .. version_changed:: 2.3

        Added the ``surrogate_then_replace`` error handler and made it the default error handler.
    """
    if isinstance(obj, binary_type):
        return obj

    # We're given a text string
    # If it has surrogates, we know because it will decode
    original_errors = errors
    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, text_type):
        try:
            # Try this first as it's the fastest
            return obj.encode(encoding, errors)
        except UnicodeEncodeError:
            if original_errors in (None, 'surrogate_then_replace'):
                # We should only reach this if encoding was non-utf8 original_errors was
                # surrogate_then_escape and errors was surrogateescape

                # Slow but works
                return_string = obj.encode('utf-8', 'surrogateescape')
                return_string = return_string.decode('utf-8', 'replace')
                return return_string.encode(encoding, 'replace')
            raise

    # Note: We do these last even though we have to call to_bytes again on the
    # value because we're optimizing the common case
    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                # Giving up
                return to_bytes('')
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        # python2.4 doesn't have b''
        return to_bytes('')
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_bytes\' nonstring parameter' % nonstring)

    return to_bytes(value, encoding, errors)


def to_text(obj, encoding='cp936' if WIN else 'utf-8' , errors=None, nonstring='simplerepr'):
    """Make sure that a string is a text string

    :arg obj: An object to make sure is a text string.  In most cases this
        will be either a text string or a byte string.  However, with
        ``nonstring='simplerepr'``, this can be used as a traceback-free
        version of ``str(obj)``.
    :kwarg encoding: The encoding to use to transform from a byte string to
        a text string.  Defaults to using 'utf-8'.
    :kwarg errors: The error handler to use if the byte string is not
        decodable using the specified encoding.  Any valid `codecs error
        handler <https://docs.python.org/2/library/codecs.html#codec-base-classes>`_
        may be specified.   We support three additional error strategies
        specifically aimed at helping people to port code:

            :surrogate_or_strict: Will use surrogateescape if it is a valid
                handler, otherwise it will use strict
            :surrogate_or_replace: Will use surrogateescape if it is a valid
                handler, otherwise it will use replace.
            :surrogate_then_replace: Does the same as surrogate_or_replace but
                `was added for symmetry with the error handlers in
                :func:`ansible.module_utils._text.to_bytes` (Added in Ansible 2.3)

        Because surrogateescape was added in Python3 this usually means that
        Python3 will use `surrogateescape` and Python2 will use the fallback
        error handler. Note that the code checks for surrogateescape when the
        module is imported.  If you have a backport of `surrogateescape` for
        python2, be sure to register the error handler prior to importing this
        module.

        The default until Ansible-2.2 was `surrogate_or_replace`
        In Ansible-2.3 this defaults to `surrogate_then_replace` for symmetry
        with :func:`ansible.module_utils._text.to_bytes` .
    :kwarg nonstring: The strategy to use if a nonstring is specified in
        ``obj``.  Default is 'simplerepr'.  Valid values are:

        :simplerepr: The default.  This takes the ``str`` of the object and
            then returns the text version of that string.
        :empty: Return an empty text string
        :passthru: Return the object passed in
        :strict: Raise a :exc:`TypeError`

    :returns: Typically this returns a text string.  If a nonstring object is
        passed in this may be a different type depending on the strategy
        specified by nonstring.  This will never return a byte string.
        From Ansible-2.3 onwards, the default is `surrogate_then_replace`.

    .. version_changed:: 2.3

        Added the surrogate_then_replace error handler and made it the default error handler.
    """
    if isinstance(obj, text_type):
        return obj

    if errors in _COMPOSED_ERROR_HANDLERS:
        if HAS_SURROGATEESCAPE:
            errors = 'surrogateescape'
        elif errors == 'surrogate_or_strict':
            errors = 'strict'
        else:
            errors = 'replace'

    if isinstance(obj, binary_type):
        # Note: We don't need special handling for surrogate_then_replace
        # because all bytes will either be made into surrogates or are valid
        # to decode.
        return obj.decode(encoding, errors)

    # Note: We do these last even though we have to call to_text again on the
    # value because we're optimizing the common case
    if nonstring == 'simplerepr':
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                # Giving up
                return u''
    elif nonstring == 'passthru':
        return obj
    elif nonstring == 'empty':
        return u''
    elif nonstring == 'strict':
        raise TypeError('obj must be a string type')
    else:
        raise TypeError('Invalid value %s for to_text\'s nonstring parameter' % nonstring)

    return to_text(value, encoding, errors)

def getLine(content):
    _c = to_text(content)
    if none_null_stringNone(_c):
        return None
    return _c.strip()

def outres(logger,res):
    assert logger
    if res and res.stdout:
        logger.info(getLine(res.stdout))
    if res and res.stderr:
        logger.info(getLine(res.stderr))
#: :py:func:`to_native`
#:      Transform a variable into the native str type for the python version
#:
#:      On Python2, this is an alias for
#:      :func:`~ansible.module_utils.to_bytes`.  On Python3 it is an alias for
#:      :func:`~ansible.module_utils.to_text`.  It makes it easier to
#:      transform a variable into the native str type for the python version
#:      the code is running on.  Use this when constructing the message to
#:      send to exceptions or when dealing with an API that needs to take
#:      a native string.  Example::
#:
#:          try:
#:              1//0
#:          except ZeroDivisionError as e:
#:              raise MyException('Encountered and error: %s' % to_native(e))
if PY3:
    to_native = to_text
else:
    to_native = to_bytes


def isNull(param):
    return not ( param and str(param).strip() )

def stringNone(param):
    return  param and str(param).upper() == 'NONE'

def none_null_stringNone(param):
    if isinstance(param,(tuple,list)):
        for i in param:
            if not (isNull(param) or stringNone(param)):
                return False
        return True
    return isNull(param) or stringNone(param)

def formatDate(format='%Y%m%d'):
    return time.strftime(format,time.localtime())

def formatDateTime():
    return formatDate('%Y%m%d%H%M%S')


def path_join(basepath,suffixpath,sep=path.sep):
    if not ( isNull(basepath) and isNull(suffixpath) ):
        if not isNull(basepath):
            basepath = basepath.strip()
            if basepath[-1] == sep:
                basepath = basepath[:-1]
        if not isinstance(suffixpath,(tuple,list)):
            suffixpath = (suffixpath,)
        s = ''
        for i in suffixpath:
            if not isNull(i):
                i = i.strip()
                if i[0] != sep:
                    i = sep + i
                s += i
        return basepath + s

def wait_until_timeout(func,timeout=30):
    increment = 5
    while( timeout > 0 and not func()):
        timeout -= increment
        time.sleep(increment)


def format_exc():
    return traceback.format_exc()


def formatErrorMsg(e):
    try:
        return 'errno:{},msg:{},args:{}'.format(str(e.errno),e.msg,e.args)
    except BaseException:
        return traceback.format_exc()



def getUnArchiveFileName(filepath):
    _filename = path.basename(filepath)
    _sub = len(_filename)
    if _filename.endswith('.tar.gz'):
        _sub = -7
    elif _filename.endswith('.zip'):
        _sub = -4
    elif _filename.endswith('.tar'):
        _sub = -4
    return _filename[:_sub]

def IsOpen(port,ip='localhost'):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect((ip,int(port)))
        return True
    except:
        return False
    finally:
        try:
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except:
            pass