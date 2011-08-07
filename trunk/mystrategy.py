# -*- coding: utf8 -*-

from strategy import *
import logging

class day_long_break_30(LONG_BREAK):#每小时中间触发
    def check(self,data,ctick):
        #print u'in check,%s:%s' % (ctick.min1,ctick.sec)
        #if ctick.min1 % 100 == 30 and ctick.sec>58 and ctick.msec==0:
        if ctick.min1 % 100 == 0 and ctick.sec==59 and ctick.msec ==0:
            logging.info(u'S:day_long_break_30:发出多头信号=%s:%s %s' % (ctick.min1,ctick.sec,ctick.msec))
            return (True,0)
        return (False,0)


class day_long_stoper_35(DATR_LONG_STOPER):#触发后5分钟平仓
    def check(self,ctick):
        #print u'in check,%s:%s:%s' % (ctick.min1,ctick.sec,ctick.msec)
        #if ctick.min1 % 100 == 30 and ctick.sec>58 and ctick.msec==0:
        if ctick.min1 % 100 == 5 and ctick.sec==59:# and ctick.msec ==0:
            logging.info(u'S:day_long_stoper_35:发出多头平仓信号=%s:%s %s' % (ctick.min1,ctick.sec,ctick.msec))
            return (True,ctick.low,False)
        return (False,0,False)

