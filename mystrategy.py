# -*- coding: utf8 -*-

import logging

from base import *
from strategy import *

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

class dl_break_nhh(LONG_BREAK): #nhhv的实现
    def check(self,data,ctick):
        pass

class dl_break_nhhv(LONG_BREAK): #nhhv的实现
    def check(self,data,ctick):
        pass

class dl_break_mll2(LONG_BREAK): #mll2的实现
    def __init__(self,length=80,vbreak=10,vrange=270,vrange2=200,tlimit=1325):
        LONG_BREAK.__init__(self)
        self.length = length
        self.vbreak = vbreak
        self.vrange = vrange
        self.vrange2 = vrange2
        self.tlimit = tlimit

    def check(self,data,ctick):
        tlow = min(data.slow[-self.length:])[-1] + self.vbreak
        ldmid = (data.d1[IHIGH][-1] + data.d1[IHIGH][-2])/2
        vhigh = data.cur_day.vhigh
        opend = data.cur_day.vopen
        drange = (vhigh - data.cur_day.vlow)[-1]
        if ctick.min1 < self.tlimit and drange < self.vrange:
            slimit = vhigh - self.vrange
        elif ctick.min1 > self.tlimit and drange < self.vrange:
            slimit = vhigh - self.vrange2
        else:
            slimit = tlow
        tlow = min(slimit,tlow,ldmid-60)
        signal = data.slow[-1] > tlow and ctick.price < tlow
        my_signal = (signal and data.sclose[-1] < tlow * 1.0015 and tlow < ldmid - 60 and data.ma13[-1] < data.ma30[-1]
                        and vhigh - tlow < opend / 33
                    )
        return (True,0) if my_signal else (False,0)
        

class dl_break_mll2v(SHORT_BREAK): #mll2v的实现
    def check(self,data,ctick):
        pass
