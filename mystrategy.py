# -*- coding: utf8 -*-

import logging

from base import *
from strategy import *
import dac

class min_long_break(LONG_BREAK):#每分钟触发
    def check(self,data,ctick):
        #print u'in check,%s:%s' % (ctick.min1,ctick.sec)
        logging.info(u'in check,%s:%s:%s' % (ctick.min1,ctick.sec,ctick.msec))
        #if ctick.min1 % 100 == 30 and ctick.sec>58 and ctick.msec==0:
        if ctick.sec <= 3:#and ctick.msec ==0:
            logging.info(u'S:min_long_break:发出多头信号=%s:%s %s' % (ctick.min1,ctick.sec,ctick.msec))
            return (True,0)
        return (False,0)


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

class dl_break_nhh(LONG_BREAK): #nhh的实现
    def __init__(self,vbreak=30,vrange=250,vopen=90,vdelay=3):
        LONG_BREAK.__init__(self)
        self.vbreak = vbreak
        self.vrange = vrange
        self.vopen = vopen
        self.vdelay = vdelay
        self.pre_high = 0  #前一分钟的日内高点
        self.cur_highx = 0  #前vdelay分钟的日内高点
        self.pre_highx = 0  #前vdelay+1分钟的日内高点
        self.pre_thigh = 0  #前一分钟突破点
        self.cur_thigh = 0
        self.last_signal = 0
        self.thigh = [0] * vdelay
    
    def check(self,data,ctick):
        opend = data.cur_day.vopen
        vlow = data.cur_day.vlow
        logging.info(u'in check dl_break_nhh')
        if ctick.switch_min:
            self.pre_thigh = self.cur_thigh
            self.pre_highx = self.thigh.pop()
            self.thigh.insert(0,self.pre_high)
            self.cur_high = self.thigh[-1] 
            thigh = self.cur_high + self.vbreak

            drange = self.cur_high - vlow
            s1 = vlow + self.vrange + self.vbreak
            slimit =  s1 if s1 > opend+self.vopen else opend+self.vopen
            
            self.cur_thigh = thigh if thigh >slimit else slimit
            #logging.info(u'当前时间=%s,thigh=%s,pre_thigh=%s' % (ctick.time,self.cur_thigh,self.pre_thigh))
            #logging.info(u'%s:%s:%s' % (data.sclose[-1],data.ma_13[-1],data.ma_30[-1]))
        #self.pre_high = data.cur_day.vhighd   
        self.pre_high = data.cur_day.vhigh #不用服务器上传过来的值，用ticks比较值
        signal = data.shigh[-1] <= self.pre_thigh and ctick.price > self.cur_thigh
        fsignal = (self.cur_thigh - vlow < opend / 33 
                and data.sclose[-3] > self.cur_thigh * 0.9966
                and data.xatr1[-1] < 2500
                and ctick.min1 > 1035
                and ctick.min1 < 1436
            )
        my_signal = signal and fsignal
        if my_signal and ctick.min1 != self.last_signal:# and ctick.min1<1300:
            logging.info(u'发出信号:%s:%s:%s:%s,self.cur_thigh=%s' % ('dl_break_nhh',ctick.time,ctick.sec,ctick.price,self.cur_thigh))
            logging.info(u'ATR1=%s,ATR30=%s,XATR1=%s,XATR30=%s' % (data.atr1[-1],data.atr30[-1],data.xatr1[-1],data.xatr30[-1]))
            self.last_signal = ctick.min1
            return (True,0)
        return (False,0)

class dl_break_nhhv(LONG_BREAK): #nhhv的实现
    def __init__(self,vbreak=30,vdelay=3,percent=100):
        LONG_BREAK.__init__(self)
        self.vbreak = vbreak
        self.percent = percent
        self.vdelay = vdelay
        self.pre_high = 0  #前一分钟的日内高点
        self.cur_highx = 0  #前vdelay分钟的日内高点
        self.pre_highx = 0  #前vdelay+1分钟的日内高点
        self.pre_thigh = 0  #前一分钟突破点
        self.cur_thigh = 0
        self.last_signal = 0
        self.thigh = [0] * vdelay
    
    def check(self,data,ctick):
        opend = data.cur_day.vopen
        vlow = data.cur_day.vlow
        if ctick.switch_min:
            self.pre_thigh = self.cur_thigh
            self.pre_highx = self.thigh.pop()
            self.thigh.insert(0,self.pre_high)
            self.cur_high = self.thigh[-1] 
            thigh = self.cur_high + self.vbreak

            vrange = data.d1[ICLOSE][-1] / self.percent
            self.cur_thigh = thigh if thigh >= vlow + vrange else vlow + vrange
            #logging.info(u'ma5=%s,ma13=%s' % (data.ma_5[-1],data.ma_13[-1]))
            #logging.info(u'当前时间=%s,cur_thigh=%s,pre_thigh=%s,thigh=%s' % (ctick.time,self.cur_thigh,self.pre_thigh,thigh))
            #logging.info(u'%s:%s:%s' % (data.sclose[-1],data.ma_13[-1],data.ma_30[-1]))
        #self.pre_high = data.cur_day.vhighd   
        self.pre_high = data.cur_day.vhigh #不用服务器上传过来的值，用ticks比较值
        signal = data.shigh[-1] <= self.pre_thigh and ctick.price > self.cur_thigh
        fsignal = (self.cur_thigh - vlow < opend / 33 
                and data.sclose[-3] > self.cur_thigh * 0.9966
                and data.xatr1[-1] < 2000
                and data.ma_5[-1] > data.ma_13[-1]
                and ctick.min1 > 1035
                and ctick.min1 < 1436
            )
        my_signal = signal and fsignal
        if my_signal and ctick.min1 != self.last_signal:# and ctick.min1<1300:
            logging.info(u'发出信号:%s:%s:%s:%s,self.cur_thigh=%s' % ('dl_break_nhh',ctick.time,ctick.sec,ctick.price,self.cur_thigh))
            logging.info(u'ATR1=%s,ATR30=%s,XATR1=%s,XATR30=%s' % (data.atr1[-1],data.atr30[-1],data.xatr1[-1],data.xatr30[-1]))
            self.last_signal = ctick.min1
            return (True,0)
        return (False,0)

class dl_break_mll2(SHORT_BREAK): #mll2的实现
    def __init__(self,length=80,vbreak=10,vrange=270,vrange2=200,tlimit=1325):
        SHORT_BREAK.__init__(self)
        self.length = length
        self.vbreak = vbreak
        self.vrange = vrange
        self.vrange2 = vrange2
        self.tlimit = tlimit
        self.pre_dlow = 0   #上一分钟日内低点
        self.pre_tlow = 0
        self.cur_tlow = 0
        self.last_signal = 0

    def check(self,data,ctick):
        ldmid = (data.d1[IHIGH][-1] + data.d1[IHIGH][-2])/2        
        vhigh = data.cur_day.vhigh
        opend = data.cur_day.vopen
        logging.info(u'in check dl_break_mll2')
        if ctick.switch_min:
            self.pre_tlow = self.cur_tlow
            self.cur_tlow = min(data.slow[-self.length:]) + self.vbreak
            #drange = vhigh - data.cur_day.vlow  #这里有点不同，用到的幅度不是上一分钟的，也用到本分钟
            drange = vhigh - self.pre_dlow
            if ctick.min1 < self.tlimit and drange < self.vrange:
                slimit = vhigh - self.vrange
            elif ctick.min1 > self.tlimit and drange < self.vrange:
                slimit = vhigh - self.vrange2
            else:
                slimit = self.cur_tlow
            logging.info(u'iorder=%s,tlimit=%s,min1=%s,drange=%s,vrange=%s,vrange2=%s,vhigh=%s,pre_dlow=%s,slimit=%s,cur_low=%s' % (ctick.iorder,self.tlimit,ctick.min1,drange,self.vrange,self.vrange2,vhigh,self.pre_dlow,slimit,self.cur_tlow))
            self.cur_tlow = min(slimit,self.cur_tlow,ldmid-60)
            #self.fsignal = (data.sclose[-1] < self.cur_tlow * 1.0015 and self.cur_tlow < ldmid - 60 and data.ma_13[-1] < data.ma_30[-1] and vhigh - self.cur_tlow < opend / 33)   #因为00归入老的一分钟,所以这里不能这么做
            logging.info(u'当前时间=%s,tlow=%s,pre_tlow=%s,slow[-1]=%s,stime[-1]=%s' % (ctick.time,self.cur_tlow,self.pre_tlow,data.slow[-1],data.stime[-1]))
            #logging.info(u'%s:%s:%s' % (data.sclose[-1],data.ma_13[-1],data.ma_30[-1]))
        #self.pre_dlow = data.cur_day.vlowd
        self.pre_dlow = data.cur_day.vlow   #不用服务器上传过来的值，用ticks比较值
        signal = data.slow[-1] >= self.pre_tlow and ctick.price < self.cur_tlow
        fsignal = (data.sclose[-1] < self.cur_tlow * 1.0015 
                and self.cur_tlow < ldmid - 60 
                and data.ma_13[-1] < data.ma_30[-1] 
                and vhigh - self.cur_tlow < opend / 33 
                and data.xatr1[-1] < 2000
                and data.xatr30[-1] < 10000
                and ctick.min1 > 944 
                and ctick.min1 < 1445
            )
        
        my_signal = signal and fsignal
        if my_signal and ctick.min1 != self.last_signal: #and ctick.min1<1300:
            logging.info(u'发出信号:%s:%s:%s:%s,self.cur_tlow=%s,close[-1]=%s' % ('dl_break_mll2',ctick.time,ctick.sec,ctick.price,self.cur_tlow,data.sclose[-1]))
            logging.info(u'ATR1=%s,ATR30=%s,XATR1=%s,XATR30=%s' % (data.atr1[-1],data.atr30[-1],data.xatr1[-1],data.xatr30[-1]))
            self.last_signal = ctick.min1
            return (True,0)
        return (False,0)


class dl_break_mll2v(SHORT_BREAK): #mll2v的实现
    def __init__(self,length=80,vbreak=10,rvrange=2./3,rvrange2=1./2,wlen=3,vmid=60,tlimit=1325):
        SHORT_BREAK.__init__(self)
        self.length = length
        self.vbreak = vbreak
        self.rvrange = rvrange
        self.rvrange2 = rvrange2
        self.wlen = wlen
        self.vmid = vmid
        self.tlimit = tlimit
        self.pre_dlow = 0   #上一分钟日内低点
        self.pre_tlow = 0
        self.cur_tlow = 0
        self.last_signal = 0
        self.vwave = 0

    def check(self,data,ctick):
        ldmid = (data.d1[IHIGH][-1] + data.d1[IHIGH][-2])/2        
        vhigh = data.cur_day.vhigh
        opend = data.cur_day.vopen
        if ctick.switch_min:
            self.vwave = (sum(data.d1[IHIGH][-self.wlen:]) - sum(data.d1[ILOW][-self.wlen:])) / self.wlen
            #vrange = min(self.vwave * self.rvrange,opend / 66)
            #vrange2 = min(self.vwave * self.rvrange2,opend / 66)
            vrange = self.vwave * self.rvrange
            vrange2 = self.vwave * self.rvrange2
            #drange = vhigh - data.cur_day.vlow  #这里有点不同，用到的幅度不是上一分钟的，也用到本分钟
            drange = vhigh - self.pre_dlow

            self.pre_tlow = self.cur_tlow
            tlow = min(data.slow[-self.length:]) + self.vbreak

            if ctick.min1 < self.tlimit and drange < vrange:
                self.cur_tlow = tlow if tlow < vhigh - vrange else vhigh - vrange
            elif ctick.min1 > self.tlimit and drange < vrange2:
                self.cur_tlow = tlow if tlow < vhigh - vrange2 else vhigh - vrange2
            else:
                self.cur_tlow = tlow
            #logging.info(u'当前时间=%s,src_tlow=%s,cur_tlow=%s,pre_tlow=%s,vrange=%s,vrange2=%s,cprice=%s,vwave=%s' % (ctick.time,tlow,self.cur_tlow,self.pre_tlow,vrange,vrange2,ctick.price,self.vwave))
            #logging.info(u'\t opend=%s,dhigh=%s' % (opend,vhigh))
        #self.pre_dlow = data.cur_day.vlowd
        self.pre_dlow = data.cur_day.vlow   #不用服务器上传过来的值，用ticks比较值
        signal = data.slow[-1] >= self.pre_tlow and ctick.price < self.cur_tlow
        fsignal = (data.sclose[-3] < self.cur_tlow * 1.0050 
                and self.cur_tlow < ldmid - self.vmid
                and data.ma_13[-1] < data.ma_30[-1] 
                and vhigh - self.cur_tlow < opend / 33 
                and data.xatr1[-1] < 2000
                and data.xatr30[-1] < 10000
                and ctick.min1 > 1000 
                and ctick.min1 < 1445
            )
        my_signal = signal #and fsignal
        if my_signal and ctick.min1 != self.last_signal: #同一分钟信号不重发
            logging.info(u'发出信号:%s:%s:%s:%s,self.cur_tlow=%s' % ('dl_break_mll2v',ctick.time,ctick.sec,ctick.price,self.cur_tlow))
            self.last_signal = ctick.min1
            return (True,0)
        return (False,0)

