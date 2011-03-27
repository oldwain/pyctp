# -*- coding: utf8 -*-

'''
    策略
    包括紧盯的合约
    目前支持手工设定标的合约，有时间时自动盘前判断主力合约

'''

import utype

from base import *


##策略类
#基类提供接口
    

'''
每个策略类必须实现两个方法:
    check(self,data,ctick)  #信号检查
        必须返回(开仓标志, 基准价)
        其中开仓标志:    0:不开仓, 1:开仓
                         基准价为开仓基准价，将用于计算开仓限价和开仓止损
    calc_target_price(self,base_price,tick_base) #计算开仓限价, 其中tick_base是每跳幅度
'''

####下单
class Order(object):
    def __init__(self,position,base_price,target_price,mytime,action_type):
        self.position = position
        self.base_price = base_price
        self.target_price = target_price
        self.mytime = mytime
        ##衍生
        self.instrument = position.instrument
        self.direction = utype.THOST_FTDC_D_Buy if position.strategy.direction==LONG else utype.THOST_FTDC_D_Sell
        ##操作类型
        assert action_type == XOPEN,u'操作类型必须是开仓'
        self.action_type = action_type
        ##
        self.volume = 0 #目标成交手数
        self.opened_volume = 0  #实际成交手数
        self.stoper = None
        self.trader_detail = []
        self.cancelled = False  #是否已经撤单

    def on_trade(self,price,volume,trade_time):
        self.opened_volume += volume
        self.trader_detail.append((price,volume,trade_time))
        self.position.re_calc()
        
    def on_close(self,price,volume,trade_time):
        self.opened_volume -= volume
        self.trade_detail.append((price,-volume,trade_time))
        self.position.re_calc()

    def on_cancel(self):    #已经撤单
        self.cancelled = True
        self.position.re_calc()

    def is_closed(self): #是否已经完全平仓
        return self.cancelled and self.opened_volume == 0


####头寸
class Position(object):
    def __init__(self,instrument,strategy):
        self.instrument = instrument
        self.strategy = strategy
        self.orders = []    #元素为Order
        self.opened_volume = 0
        self.locked_volume = 0  #被当前头寸锁定的(包括持仓的和发出未成交的)

    def calc_remained_volume(self):   #用来计算Position的当次可开仓数
        self.re_calc()
        #剩余开仓总数 = 策略持仓限量 - 已开仓数，若小于0则为0
        remained = self.strategy.max_holding - self.locked_volume if self.strategy.max_holding > self.locked_volume else 0
        #本次可开仓数 = 策略单次开仓数 和 剩余开仓总数 的小者
        return self.strategy.open_volume if self.strategy.open_volume <=  remained else remained

    def re_calc(self): #
        self.orders = [order for order in self.orders if not order.is_closed()]
        self.opened_volume = sum[order.opened_volume for order in self.orders]
        self.locked_volume = sum[order.volume for order in self.orders]

    def add_order(self,order):
        self.orders.append(order)


###突破类策略
###突破类策略以当前价为基准价，以一定额度的加价作为开仓限价以确保开仓，同时根据基准价来计算止损
MAX_OVERFLOW = 60   #最大溢点，即开仓时加价跳数
VALID_LENGTH = 120  #行情跳数, 至少两分钟(视行情移动为准)
class BREAK(object):    #策略标记
    pass

class LONG_BREAK(BREAK):    #多头突破策略
    def __init__(self,max_overflow=60,valid_length=VALID_LENGTH):
        self.direction = LONG
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'多头突破基类'

    def calc_target_price(self,base_price,tick_base):    #计算开单加价
        return base_price + tick_base * self.max_overflow

class SHORT_BREAK(BREAK):   #空头突破策略
    def __init__(self,max_overflow=60,valid_length=VALID_LENGTH):
        self.direction = SHORT
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'空头突破基类'

    def calc_target_price(self,base_price,tick_base):#计算开仓加价
        return base_price - tick_base * self.max_overflow


###回归类策略
###回归类策略以计算所得价为基准价，并挂单来做钓鱼式成交
class ENTRY(object):    #回归策略标记
    def calc_target_price(self,base_price,tick_base):    #回归策略不加价
        return base_price

class LONG_ENTRY(ENTRY):    #多头回归策略
    def __init__(self,valid_length=VALID_LENGTH):
        self.direction = LONG
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'多头回归基类'


class SHORT_ENTRY(ENTRY):    #空头回归策略
    def __init__(self,valid_length=VALID_LENGTH):
        self.direction = SHORT
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'空头回归基类'


#####具体策略
class day_long_break(LONG_BREAK):
    def check(self):
        return (0,0)

class day_short_break(SHORT_BREAK):
    def check(self):
        return (0,0)


##止损类(平仓不允许钓鱼，必然直接平仓)
'''
    每个具体止损类必须实现三个方法
        __init__方法签名必须是(self,data,**kwargs),或者其它参数被fcustom化
        check方法签名为(self,ctick)
            必须返回(平仓标志, 基准价)
            其中平仓标志:    0:不平仓, 1:平仓
                         基准价为平仓基准价，将用于计算平仓限价
        calc_target_price(self,base_price,tick_base) #计算平仓限价, 其中tick_base是每跳幅度
'''

STOP_VALID_LENGTH = 2   #最好是1秒后就撤单, 以便及时追平

class STOPER(object):    #离场类标记
    '''
        对于必须要实现断点恢复的stoper类，必须使用self.base_line和self.cur_stop作为判断标准
    '''
    def __init__(self):
        self.cur_stop = 0
        self.base_line = 0

    def get_cur_stop(self):
        return self.cur_stop

    def set_cur_stop(self,cur_stop):
        self.cur_stop = cur_stop

    def get_base_line(self):
        return self.base_line

    def set_base_line(self,base_line):
        self.base_line = base_line

    
class LONG_STOPER(STOPER):
    def __init__(self,max_overflow=120,valid_length=STOP_VALID_LENGTH):
        self.direction = SHORT
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'多头离场基类'

    def calc_target_price(self,base_price,tick_base):#计算多头平仓加价,
        return base_price - tick_base * self.max_overflow

class SHORT_STOPER(STOPER):
    def __init__(self,max_overflow=120,valid_length=STOP_VALID_LENGTH):
        self.direction = LONG
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'空头离场基类'

    def calc_target_price(self,base_price,tick_base):#计算空头平仓加价,
        return base_price + tick_base * self.max_overflow

class DATR_LONG_STOPER(LONG_STOPER):#日ATR多头止损
    def __init__(self,data,bline,rbase=0.12,rkeeper=0.2,rdrawdown = 0.4):
        self.data = data
        self.set_base_line(bline)
        self.thigh = bline
        self.ticks = 0
        self.name = u'多头日ATR止损,初始止损=%s,保本=%s,最大回撤=%s' % (rbase,rkeeper,rdrawdown)
        self.max_drawdown = int(data.atrd1 * rdrawdown / XBASE + 0.5)
        self.keeper = int(data.atrd1 * rkeeper / XBASE + 0.5)
        self.set_cur_stop(bline - int(data.atrd1 * rbase / XBASE + 0.5))

    def check(self,tick):
        '''
            必须返回(平仓标志, 基准价)
            基准价为0则为当前价
        '''
        if tick.price < self.get_cur_stop():
            return (1,tick.price)
        if self.get_cur_stop()< self.get_base_line() and tick.price > self.get_base_line() + self.keeper:
            ##提升保本
            self.set_cur_stop(self.get_base_line())
        if tick.price > self.thigh:
            self.thigh = tick.price
            if self.thigh - self.max_drawdown > self.get_cur_stop():
                self.set_cur_stop(self.thigh - self.max_drawdown)
        return (0,0)       

class DATR_SHORT_STOPER(SHORT_STOPER):#日ATR空头止损
    def __init__(self,data,bline,rbase=0.12,rkeeper=0.2,rdrawdown = 0.4):
        self.data = data
        self.set_base_line(bline)
        self.tlow = bline
        self.itime = len(self.data.sclose)  #time的索引，用于计算耗时
        self.name = u'空头日ATR止损,初始止损=%s,保本=%s,最大回撤=%s' % (rbase,rkeeper,rdrawdown)
        self.max_drawdown = int(data.atrd1 * rdrawdown / XBASE + 0.5)
        self.keeper = int(data.atrd1 * rkeeper / XBASE + 0.5)
        self.set_cur_stop(bline + int(data.atrd1 * rbase / XBASE + 0.5))

    def check(self,tick):
        '''
            必须返回(平仓标志, 基准价)
            基准价为0则为当前价
        '''
        if tick.price > self.get_cur_stop():
            return (1,tick.price)
        if self.get_cur_stop()> self.get_base_line() and tick.price < self.get_base_line() - self.keeper:
            ##提升保本
            self.set_cur_stop(self.get_base_line())
        if tick.price < self.tlow:
            self.tlow = tick.price
            if self.tlow - self.max_drawdown > self.get_cur_stop():
                self.set_cur_stop(self.tlow - self.max_drawdown)
        return (0,0)       


datr_long_stoper_12 = fcustom(DATR_LONG_STOPER,base=0.12)
datr_short_stoper_12 = fcustom(DATR_SHORT_STOPER,base=0.12)


class STRATEGY(object):#策略基类, 单纯包装
    def __init__(self,
                opener, #开仓类(注意，不是对象)
                closer, #平仓类(注意，不是对象)
                open_volume, #每次开仓手数   
                max_holding, #最大持仓手数 
            ):
        self.opener = opener()  #单一策略可共享开仓对象
        self.closer = closer    #平仓对象必须用开仓时的上下文初始化
        self.open_volume = open_volume
        self.max_holding = max_holding

    def get_name(self):
        return u'%s_%s_%s_%s' % (self.opener.name,self.closer.name,self.open_volume,self.max_holding)
