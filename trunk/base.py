#-*- coding:utf-8 -*-

IDATE,ITIME,IOPEN,ICLOSE,IHIGH,ILOW,IVOL,IHOLDING = 0,1,2,3,4,5,6,7

#多空标志
LONG,SHORT,EMPTY = -1,1,0   #多仓出钱,淡仓收钱
#开平仓的标志
XOPEN,XCLOSE = -1,1 #开仓,平仓


import sys
from functools import partial

def inverse_direction(direction):
    return LONG if direction == SHORT else SHORT

def fcustom(func,**kwargs):
    ''' 根据kwargs设置func的偏函数,并将此偏函数的名字设定为源函数名+所固定的关键字参数名
    '''
    pf = partial(func,**kwargs)
    #pf.name = pf.func.func_name
    pf.paras = ','.join(['%s=%s' % item for item in pf.keywords.items()])
    pf.__name__ = '%s:%s' % (func.__name__,pf.paras)
    return pf

def func_name(func):    #取到真实函数名. 可能只适用于python2.x
    if 'name' in func.__dict__:
        return func.name
    cfunc = func
    while(isinstance(cfunc,functools.partial)):
        cfunc = cfunc.func
    return str(cfunc)[10:-15]



class BaseObject(object):
    def __init__(self,**kwargs):
        self.__dict__.update(kwargs)

    def has_attr(self,attr_name):
        return attr_name in self.__dict__

    def get_attr(self,attr_name):
        return self.__dict__[attr_name]

    def set_attr(self,attr_name,value):
        self.__dict__[attr_name] = value

    def __repr__(self):
        return 'BaseObject'


class CommonObject(BaseObject):
    def __init__(self,id,**kwargs):
        BaseObject.__init__(self,**kwargs)
        self.id = id

    def __repr__(self):
        return 'CommonObject'


LINELENGTH = 60
def linelog(msg):   #在同一行覆盖显示日志输出
    sys.stdout.write(unicode((u'\r%s%s' % (msg,' ' * (LINELENGTH - len(msg)))))) #.encode('gbk'))  #适应输出编码为gbk

