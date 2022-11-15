from . import setpath
import re
import datetime
import io
from lib.dsv import writer, reader
from lib import argsparse
import functions
import lib.inoutparsing as csvargs

def strsplit(*args): ###splits the first arguments
    """
    
    .. function:: strsplit(str[,formatting options]) -> [C1,C2,....]

    Splits *str* according to *formatting options*, default behavior is to split on space.
    It is a multiset operator that returns one row.

    .. seealso::

        * :ref:`tutmultiset` functions

    .. _formattingopts:

    Formatting options:

    :dialect: *tsv/csv*

        Formats field as tab/comma separated values with minimal quoting

    :delimiter:

        A string used to separate fields. It defaults to ' '

    :doublequote: *t/f*

        Controls how instances of quotechar appearing inside a
        field should be themselves be quoted. When True, the
        character is doubled. When False, the escapechar is used as
        a prefix to the quotechar. It defaults to True.
        On output, if doublequote is False and no escapechar is set,
        Error is raised if a quotechar is found in a field

    :escapechar:

        A one-character string used by the writer to escape the delimiter
        if quoting is set to QUOTE_NONE and the quotechar if doublequote is False.
        On reading, the escapechar removes any special meaning from the following
        character. It defaults to None, which disables escaping.

    :quotechar:

        A one-character string used to quote fields containing special characters,
        such as the delimiter or quotechar, or which contain new-line characters.
        It defaults to '"'.

    :quoting:

        Controls when quotes should be generated by the writer and recognized by
        the reader. It can take on any of the QUOTE_* constants and defaults to
        QUOTE_MINIMAL. Possible values are QUOTE_ALL, QUOTE_NONE, QUOTE_MINIMAL, QUOTE_NONNUMERIC

    :skipinitialspace: *t/f*

        When True, whitespace immediately following the delimiter is ignored. The default is False

    :Returned multiset schema:
        - *C1,C2...*
            Text values produced from splitting.

    Examples:

    >>> sql("select strsplit('First,Second,Third', 'dialect:csv')")
    C1    | C2     | C3
    ----------------------
    First | Second | Third
    >>> sql("select strsplit('-First-%Second%-Third-','delimiter:%','quotechar:-')")
    C1    | C2     | C3
    ----------------------
    First | Second | Third

.. doctest::
    :hide:

    >>> sql("select strsplit('-First-%Second%-Third-','quotechar:-p')")  #doctest:+ELLIPSIS +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
    ...
    MadisError: Madis SQLError:
    "quotechar" must be an 1-character string

    """    
    if len(args)<1:
        raise functions.OperatorError("strsplit"," no input")

    arg=args[0]
    args=args[1:]
    try:
        largs, kargs = argsparse.parse(args,csvargs.boolargs,csvargs.nonstringargs,csvargs.needsescape)
    except Exception as e:
        raise functions.MadisError(e)
    if 'dialect' not in kargs:
        kargs['dialect']=csvargs.defaultcsv()
        if 'delimiter' not in kargs:
            kargs['delimiter']=' '

    if len(largs)>0:
        raise functions.OperatorError("strsplit","strsplit operator: Unknown argument %s" %(''.join(largs)))
    f=io.StringIO()
    
    f.write(arg)
    f.seek(0)
    try:
        r=reader(f,**kargs)
    except Exception as e:
        raise functions.MadisError(e)
    first=True
    
    for row in r:
        if first:
            first=False
            yield tuple("C"+str(i) for i in range(1, len(row) + 1))
        yield row
    if first:
        first=False
        yield ["C1"]
    f.close()
    

strsplit.registered=True

def strsplitv(*args): ###splits the first arguments
    """
    .. function:: strsplitv(str[,formatting options]) -> [C1]

    Splits in rows *str* according to *formatting options*, default behavior is to split on space.
    It is a multiset operator that returns one column but many rows. :ref:`Formatting options<formattingopts>` are like in :func:`strsplit` function.

    .. seealso::

        * :ref:`tutmultiset` functions


    >>> sql("select strsplitv('First,Second,Third','dialect:csv')")
    C1
    ------
    First
    Second
    Third
    >>> sql("select strsplitv('First Second Third')")
    C1
    ------
    First
    Second
    Third
    """
    if len(args)<1:
        raise functions.OperatorError("strsplitv","strsplit operator: no input")
    arg=args[0]
    args=args[1:]
    try:
        largs, kargs = argsparse.parse(args,csvargs.boolargs,csvargs.nonstringargs,csvargs.needsescape)
    except Exception as e:
        raise functions.MadisError(e)
    if 'dialect' not in kargs:
        kargs['dialect']=csvargs.defaultcsv()
        if 'delimiter' not in kargs:
            kargs['delimiter']=' '

    if len(largs)>0:
        raise functions.OperatorError("strsplitv","strsplit operator: Unknown argument %s" %(''.join(largs)))
    f=io.StringIO()

    f.write(arg)
    f.seek(0)

    try:
        r=reader(f,**kargs)
    except Exception as e:
        raise functions.MadisError(e)
    first=True

    for row in r:
        if first:
            first=False
            yield ("C1",)
        for el in row:
            yield [el]
    if first:
        first=False
        yield ("C1",)
    f.close()
strsplitv.registered=True

def strjoin(*args):

    """
    .. function:: strjoin(value1,value2,....[,'params',formatting options])

    Returns a string with *value1,value2,....* formatted according to :ref:`formatting options<formattingopts>`.
    Literal parameter 'params' must precede *formating options*. Default formatting is comma separated values.

    Examples:

    >>> sql("select strjoin('First','Second','Third',100) as joinedvals")
    joinedvals
    -----------------------
    First,Second,Third,100
    >>> sql("select strjoin('First','Second','Third',100,'params','delimiter: ') as joinedvals")
    joinedvals
    -----------------------
    First Second Third 100
    >>> sql("select strjoin('lola',2,10,'llalallall','params','delimiter:%','quoting:QUOTE_ALL') as joinedvals")
    joinedvals
    -----------------------------
    "lola"%"2"%"10"%"llalallall"
    >>> sql("select strjoin('value, with delimiter ',2,10,'new','params','dialect:csv') as joinedvals")
    joinedvals
    ----------------------------------
    "value, with delimiter ",2,10,new
    """
    if None in args:
        return None
    sargs=[]
    params=False
    for i in range(len(args)):
        if args[i]=='params':
            args=args[(i+1):]
            params=True
            break
        else:
            sargs.append(args[i])
    try:
        if params:
            largs, kargs = argsparse.parse(args,csvargs.boolargs,csvargs.nonstringargs,csvargs.needsescape)
        else:
            largs=[]
            kargs=dict()
    except Exception as e:
        raise functions.MadisError(e)
    if len(largs)>0:
        raise functions.OperatorError("strjoin","Unknown argument %s" %(''.join(largs)))
    if 'dialect' not in kargs:
        kargs['dialect']=csvargs.defaultcsv()
    f=io.StringIO()
    try:
        csvprinter=writer(f,**kargs)
    except Exception as e:
        raise functions.MadisError(e)
    csvprinter.writerow(sargs)
    f.seek(0)
    s=f.read()
    return s


strjoin.registered=True


def dateformat(*args):

    """
    .. function:: dateformat(date[,inpformat,outformat])

    Returns *date* formatted with *outformat*. Default *inpformat* is %d-%m-%y and default
    *outformat* is %Y-%m-%d. To change *inpformat* just provide as second parameter the input format.
    To change *outformat*, both format parameters must be provided. If date is not formatted according
    to *inpformat* null value is returned.
    
    Check `formatting pattern <http://docs.python.org/library/time.html?#strftime-strptime-behavior>`_ details
    
    
    Examples:
    
    >>> sql("select dateformat('28-01-09') as date")
    date
    ----------
    2009-01-28

    When date doesn't meet the format null is returned

    >>> sql("select dateformat('32-01-09') as date")
    date
    ----
    None
    >>> sql("select dateformat('Thu, 28 Jun 2001 14:17:15 +0000','%a, %d %b %Y %H:%M:%S +0000') as date")
    date
    ----------
    2001-06-28
    >>> sql("select dateformat('28-01-09','%d-%m-%y','%x') as date")
    date
    --------
    01/28/09
    """
    fromf='%d-%m-%y'
    tof='%Y-%m-%d'
    if len(args)<1:
        raise functions.OperatorError("dateformat","No input")
    if None in args:
        return None
    if len(args)>1:
        fromf=args[1]
    if len(args)>2:
        tof=args[2]
    dt=args[0]
    try:
        dtobj=datetime.datetime.strptime(dt,fromf)
        ret=datetime.datetime.strftime(dtobj,tof)
    except ValueError as e:
        return None
    except Exception as e:
        raise functions.OperatorError("dateformat",e)
    return ret


dateformat.registered=True



if not ('.' in __name__):
    """
    This is needed to be able to test the function, put it at the end of every
    new function you create
    """
    import sys
    from . import setpath
    from functions import *
    testfunction()
    if __name__ == "__main__":
        reload(sys)
        sys.setdefaultencoding('utf-8')
        import doctest
        doctest.testmod()
