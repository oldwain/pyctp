# -*- coding: utf8 -*-

import logging

from base import *
from strategy import *
import dac

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

class day_short_stoper_35(DATR_SHORT_STOPER):#触发后5分钟平仓
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

class dl_break_mll2(SHORT_BREAK): #mll2的实现
    def __init__(self,length=80,vbreak=10,vrange=270,vrange2=200,tlimit=1325):
        SHORT_BREAK.__init__(self)
        self.length = length
        self.vbreak = vbreak
        self.vrange = vrange
        self.vrange2 = vrange2
        self.tlimit = tlimit
        self.pre_tlow = 0
        self.cur_tlow = 0
        self.last_min = 0
        self.last_signal = 0

    def check(self,data,ctick):
        ldmid = (data.d1[IHIGH][-1] + data.d1[IHIGH][-2])/2        
        vhigh = data.cur_day.vhigh
        opend = data.cur_day.vopen
        if ctick.time != self.last_min:
            self.last_min = ctick.time
            self.pre_tlow = self.cur_tlow
            self.cur_tlow = min(data.slow[-self.length:]) + self.vbreak
            drange = vhigh - data.cur_day.vlow
            if ctick.min1 < self.tlimit and drange < self.vrange:
                slimit = vhigh - self.vrange
            elif ctick.min1 > self.tlimit and drange < self.vrange:
                slimit = vhigh - self.vrange2
            else:
                slimit = self.cur_tlow
            self.cur_tlow = min(slimit,self.cur_tlow,ldmid-60)
            #self.fsignal = (data.sclose[-1] < self.cur_tlow * 1.0015 and self.cur_tlow < ldmid - 60 and data.ma_13[-1] < data.ma_30[-1] and vhigh - self.cur_tlow < opend / 33)   #因为00归入老的一分钟,所以这里不能这么做
            #logging.info(u'当前时间=%s,tlow=%s,pre_tlow=%s' % (ctick.time,self.cur_tlow,self.pre_tlow))
            #logging.info(u'%s:%s:%s' % (data.sclose[-1],data.ma_13[-1],data.ma_30[-1]))
        signal = data.slow[-1] > self.pre_tlow and ctick.price < self.cur_tlow
        fsignal = (data.sclose[-1] < self.cur_tlow * 1.0015 
                and self.cur_tlow < ldmid - 60 
                and data.ma_13[-1] < data.ma_30[-1] 
                and vhigh - self.cur_tlow < opend / 33 
                #and data.xatr1[-1] < 2000
                #and data.xatr30[-1] < 10000
                and ctick.min1 > 944 
                and ctick.min1 < 1445
            )
        my_signal = signal and fsignal
        if my_signal and ctick.time != self.last_signal and ctick.time<1300:
            logging.info(u'发出信号:%s:%s:%s:%s,self.cur_tlow=%s' % ('dl_break_mll2',ctick.time,ctick.sec,ctick.price,self.cur_tlow))
            logging.info(u'ATR1=%s,ATR30=%s,XATR1=%s,XATR30=%s' % (data.atr1[-1],data.atr30[-1],data.xatr1[-1],data.xatr30[-1]))
            self.last_signal = ctick.time
            return (True,0)
        return (False,0)


class dl_break_mll2v(SHORT_BREAK): #mll2v的实现
    def __init__(self,length=80,vbreak=10,rvrange=4./3,rvrange2=2./3,wlen=30,vmid=60,tlimit=1325):
        SHORT_BREAK.__init__(self)
        self.length = length
        self.vbreak = vbreak
        self.rvrange = rvrange
        self.rvrange2 = rvrange2
        self.wlen = wlen
        self.vmid = vmid
        self.tlimit = tlimit
        self.pre_tlow = 0
        self.cur_tlow = 0
        self.last_min = 0
        self.last_signal = 0
        self.vwave = 0

    def check(self,data,ctick):
        ldmid = (data.d1[IHIGH][-1] + data.d1[IHIGH][-2])/2        
        vhigh = data.cur_day.vhigh
        opend = data.cur_day.vopen
        if ctick.time != self.last_min:
            self.vwave = (sum(data.d1[IHIGH][-wlen:]) - sum(data.d1[ILOW][-wlen])) / wlen
            vrange = min(self.vwave * rvrange,opend / 66)
            vrange2 = min(self.vwave * rvrange2,opend / 66)
            drange = vhigh - data.cur_day.vlow

            self.last_min = ctick.time
            self.pre_tlow = self.cur_tlow
            tlow = min(data.slow[-self.length:]) + self.vbreak

            if ctick.min1 < self.tlimit and drange < vrange:
                self.cur_tlow = tlow if tlow < vhigh - vrange else vhigh - vrange
            elif ctick.min1 > self.tlimit and drange < vrange2:
                self.cur_tlow = tlow if tlow < vhigh - vrange2 else vhigh - vrange2
            else:
                self.cur_tlow = tlow
            logging.info(u'当前时间=%s,tlow=%s,pre_tlow=%s' % (ctick.time,self.cur_tlow,self.pre_tlow))

        signal = data.slow[-1] > self.pre_tlow and ctick.price < self.cur_tlow
        fsignal = (data.sclose[-3] < self.cur_tlow * 1.0050 
                and self.cur_tlow < ldmid - self.vmid
                and data.ma_13[-1] < data.ma_30[-1] 
                and vhigh - self.cur_tlow < opend / 33 
                and data.xatr1[-1] < 2000
                and data.xatr30[-1] < 10000
                and ctick.min1 > 1000 
                and ctick.min1 < 1445
            )
        my_signal = signal and fsignal
        if my_signal and ctick.time != self.last_signal and ctick.time<1300:
            logging.info(u'发出信号:%s:%s:%s:%s,self.cur_tlow=%s' % ('dl_break_mll2',ctick.time,ctick.sec,ctick.price,self.cur_tlow))
            self.last_signal = ctick.time
            return (True,0)
        return (False,0)

