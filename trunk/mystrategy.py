# -*- coding: utf8 -*-

from strategy import *

class day_long_break_30(LONG_BREAK):#每小时中间触发
    def check(self,data,ctick):
        #print u'in check,%s:%s' % (ctick.min1,ctick.sec)
        if ctick.min1 % 100 == 30 and ctick.sec>58 and ctick.msec==0:
            print 'in signal=%s:%s %s' % (ctick.min1,ctick.sec,ctick.msec)
            return (1,0)
        return (0,0)

