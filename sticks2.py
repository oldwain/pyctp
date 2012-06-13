# -*- coding: utf-8 -*-

import re
import os.path
import logging

from base import *
import sticks    #使用stick中已经完成的部分功能
import hreader
import strategy


LENGTH_THRESHOLD = 25000    #主力合约的ticks阈值超过


class TickAgent(object):#ticks数据管理,只管理一个合约,并最多测试一个Strategy
    def __init__(self,fname,data_path=hreader.DATA_PATH,pattern='\d{8}_tick.txt',tick_base=2):
        self.fname = fname
        self.data_path = data_path
        self.pattern = pattern
        self.rpattern = re.compile(pattern,re.IGNORECASE)
        self.mtickss = {}   #dict方式
        self.stickss = []   #顺序方式
        self.tick_base = 2  #最小行情单位
        self.closers = []    #已经开仓后需要追踪的closer
        self.trades = []

    def load(self):
        '''
            按顺序加载fname下的ticks数据.
            fname必须为IF1201这种格式
        '''
        sub_path = '%s%s' % (self.data_path,self.fname)
        tdates = sorted([int(os.path.splitext(name)[0][:8]) for name in os.listdir(sub_path) if self.rpattern.search(name)])
        for tdate in tdates:
            cticks = hreader.read_ticks(self.fname,tdate)
            self.mtickss[tdate] = DTicks(self.fname,tdate,cticks)
            self.stickss.append(self.mtickss[tdate])

    def run(self,mystrategy,tbegin=0,tend=99999999,dfilter=lambda dt:len(dt)<LENGTH_THRESHOLD):#起止日
        trades = []
        env = BaseObject(holdings=[],to_open=[],to_close=[],cur_inst=None,iorder=0) #holding是当前持仓，to_open/close是当前信号
        for dt in self.stickss:
            if dt.tdate < tbegin or dt.tdate > tend or dfilter(dt):
                continue
            ##主循环
            self.run_day(env,mystrategy,dt)
        return self.trades

    def run_day(self,env,mystrategy,dticks):#
        logging.info('run day:%s' % (dticks.tdate))
        env.cur_inst = BaseObject(cur_day=BaseObject(vhigh=0,vlow=99999999),ticks=[],prices=[],bids=[],asks=[],deltas=[],tick_base=2)
        for ctick in dticks.ticks:
            ctick.iorder = env.iorder
            env.iorder += 1
            env.cur_inst.ticks.append(ctick)
            env.cur_inst.prices.append(ctick.price)
            env.cur_inst.bids.append(ctick.bid_price)
            env.cur_inst.asks.append(ctick.ask_price)
            env.cur_inst.deltas.append(ctick.ask_price-ctick.bid_price)
            if ctick.price > env.cur_inst.cur_day.vhigh:
                env.cur_inst.cur_day.vhigh = ctick.price
            if ctick.price < env.cur_inst.cur_day.vlow:
                env.cur_inst.cur_day.vlow = ctick.price
            #先平
            #后开
            self.match_close(env,ctick)  #动作
            self.match_open(mystrategy,env,ctick)  #动作
            self.check_close(mystrategy,env,ctick)
            self.check_open(mystrategy,env,ctick)

    def check_open(self,mystrategy,env,ctick):   #
        if env.holdings or env.to_open: #如果持仓或即将持仓则不发后面信号，即要求一次开齐
            return 
        mysignal = mystrategy.opener.check(env.cur_inst,ctick)
        if mysignal[0] != 0:#发出信号
            base_price = mysignal[1] if mysignal[1]>0 else ctick.price
            base_stop = mysignal[2] if len(mysignal)>2 else 0
            env.to_open = [(BaseObject(
                                         tick = ctick,
                                         strategy = mystrategy,
                                         base_price = base_price,
                                         base_stop = base_stop,
                                         target_price = mystrategy.opener.calc_target_price(base_price,self.tick_base),
                                         valid_length = mystrategy.opener.get_valid_length(), #有效的ticks数
                                         direction = mystrategy.opener.direction,
                                        )
                             )]

    def check_close(self,mystrategy,env,ctick):
        if env.to_close:
            return
        for closer in self.closers:
            csignal = closer.check(ctick)
            base_price = csignal[1] if csignal[1]>0 else ctick.price
            if csignal[0] != 0:    #平仓
                env.to_close=[(BaseObject(
                                     tick = ctick,
                                     opened = closer.opened,#closer的开仓信息
                                     base_price = base_price,
                                     target_price = closer.calc_target_price(base_price,self.tick_base),
                                     direction = closer.direction,
                                  )
                             )]
                break


    def match_close(self,env,ctick):
        #close必须成交
        if not env.to_close:
            return
        if env.to_close[0].direction == SHORT:  #以较差价格成交, 滑点不利
            pclose = ctick.price if ctick.price <= ctick.bid_price else ctick.bid_price
        else:
            pclose = ctick.price if ctick.price >= ctick.ask_price else ctick.ask_price
        opened = env.to_close[0].opened
        mytrade = Trade(opened.tick,opened.price,ctick,pclose,opened.direction)
        self.trades.append(mytrade)
        env.to_close = []
        self.closers = []


    def match_open(self,mystrategy,env,ctick):
        if not env.to_open:
            return
        topen = env.to_open[0]
        if ctick.iorder > topen.tick.iorder+topen.valid_length:    #有效期过
            env.to_open=[]
            return 
        dealed = False
        if topen.direction == SHORT:  #
            mk_price = ctick.price if ctick.price <= ctick.bid_price else ctick.bid_price
            if topen.target_price <= mk_price:   #成交
                dealed = True
        else:   
            mk_price = ctick.price if ctick.price >= ctick.ask_price else ctick.ask_price
            if topen.target_price >= mk_price:  #成交
                dealed = True
        if dealed == True:
            topen.price = mk_price
            self.closers = [closer(env,topen.base_price,opened=topen,tick_base=self.tick_base) for closer in mystrategy.closers]


    def get_dticks(self,tdate):
        return self.mtickss[tdate] if tdate in self.mtickss else None


class Trade(object):
    def __init__(self,open_tick,open_price,close_tick,close_price,direction,tax=4):
        self.open_tick = open_tick
        self.close_tick = close_tick
        self.open_price = open_price
        self.close_price = close_price
        self.direction = direction
        self.tax = tax

    def get_profit(self):
        delta = self.close_price - self.open_price
        return delta - self.tax if self.direction==LONG else -delta - self.tax

    def get_holding_length(self):
        return self.close_tick.iorder - self.open_tick.iorder



class DTicks(object):#日tick结构
    def __init__(self,fname,tdate,ticks):
        self.fname = fname
        self.tdate = tdate
        self.ticks = ticks

    def __len__(self):
        return len(self.ticks)


class T_LONG(strategy.BREAK):
    direction = LONG
    def __init__(self,bid_ticks=3,valid_length=60):
        self.bid_ticks = bid_ticks  #买入超价
        self.valid_length = valid_length

    def calc_target_price(self,base_price,tick_base):
        return base_price + tick_base * self.bid_ticks

    def get_valid_length(self):
        return self.valid_length


    def check(self,data,ctick):
        return (False,0)


class T_SHORT(strategy.BREAK):
    direction = SHORT
    def __init__(self,ask_ticks=3,valid_length=60):
        self.ask_ticks = ask_ticks  #买入超价
        self.valid_length = valid_length

    def calc_target_price(self,base_price,tick_base):
        return base_price - tick_base * self.ask_ticks

    def get_valid_length(self):
        return self.valid_length

    def check(self,data,ctick):
        return (False,0)    

class T_LONG_DELTA(T_LONG):
    def __init__(self,delta=16,bid_ticks=3,valid_length=60):
        T_LONG.__init__(self,bid_ticks,valid_length)
        self.delta = delta

    def check(self,data,ctick):
        self.cur_tick = ctick
        if ctick.ask_price - ctick.bid_price > self.delta:
            return (True,ctick.bid_price,ctick.bid_price - 20)
        return (False,0)

class T_LONG_MOVING_STOPER(strategy.LONG_STOPER):
    def __init__(self,data,bline,max_overflow=strategy.MAX_CLOSE_OVERFLOW,valid_length=strategy.STOP_VALID_LENGTH,opened=None,tick_base=2,base_lost=10):
        strategy.LONG_STOPER.__init__(self,data,bline)
        self.direction = LONG
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'空头离场基类'
        self.opened = opened
        self.base_stop = opened.base_stop if opened!=None else opened.base_price - base_lost*tick_base
        #self.cur_stop = self.base_stop
        self.set_base_line(self.base_stop)
        self.thigh = opened.base_price
        self.tick_base = tick_base


    def check(self,tick):
        if tick.price < self.get_base_line() or tick.min1>1500:
            return (True,tick.price,False)
        if tick.price >= self.thigh + self.tick_base * 2:
            self.set_base_line(self.get_base_line() + (tick.price - self.thigh)/2)
            self.thigh = tick.price 
            return (False,0,True)

        return (False,0,False)


tstrategy = strategy.STRATEGY('TEST',T_LONG_DELTA,[T_LONG_MOVING_STOPER],1,1)
