# -*- coding: utf8 -*-

'''
    策略
    包括紧盯的合约
    目前支持手工设定标的合约，有时间时自动盘前判断主力合约

'''

import logging

import UserApiType as utype


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
        self.base_price = base_price        #开仓基准价
        self.target_price = target_price    #开仓加价部分
        self.mytime = mytime
        ##衍生
        self.instrument = position.instrument
        self.direction = utype.THOST_FTDC_D_Buy if position.strategy.direction==LONG else utype.THOST_FTDC_D_Sell
        ##操作类型
        assert action_type == XOPEN,u'操作类型必须是开仓'
        self.action_type = action_type
        ##
        self.volume = 0 #目标成交手数,锁定总数
        self.opened_volume = 0  #实际成交手数
        self.stoper = None
        self.trade_detail = []
        self.cancelled = False  #是否已经撤单

    def on_trade(self,price,volume,trade_time):
        ''' 返回是否完全成交
        '''
        logging.info(u'成交纪录:price=%s,volume=%s,trade_time=%s' % (price,volume,trade_time))
        self.opened_volume += volume
        if self.volume < self.opened_volume:    #因为cancel和成交的时间差导致的
            self.volume = self.opened_volume
        logging.info(u'price=%s,volume=%s,self.opened_volume=%s,is_closed=%s' % (price,volume,self.opened_volume,self.is_closed()))
        self.trade_detail.append((price,volume,trade_time))
        self.position.re_calc()
        return self.opened_volume == self.volume
        
    def on_close(self,price,volume,trade_time):
        self.opened_volume -= volume
        self.trade_detail.append((price,-volume,trade_time))
        logging.info('on close')
        self.position.re_calc()

    def on_cancel(self):    #已经撤单
        self.cancelled = True
        self.volume = self.opened_volume    #不会再有成交回报
        logging.debug('O_OC:on cancel')
        self.position.re_calc()

    def is_closed(self): #是否已经完全平仓
        return self.cancelled and self.opened_volume == 0

    def get_opener(self):
        return self.position.strategy.opener

    def get_stoper(self):
        return self.stoper

    def get_strategy_name(self):
        return self.position.strategy.name

    def __str__(self):
        return u'Order_A: 合约=%s,开仓策略=%s,方向=%s,目标数=%s,开仓数=%s,状态=%s' % (self.instrument.name,
                self.get_strategy_name(),
                u'多' if self.direction==utype.THOST_FTDC_D_Buy else u'空',
                self.volume,
                self.opened_volume,
                u'无效' if self.cancelled else u'有效',
            )

####头寸
class Position(object):
    def __init__(self,instrument,strategy):
        self.instrument = instrument
        self.strategy = strategy
        self.orders = []    #元素为Order
        self.opened_volume = 0
        self.locked_volume = 0  #被当前头寸锁定的(包括持仓的和发出未成交的)

    def calc_open_volume(self):   
        '''
            计算Position的当次可开仓数. 与保证金无关，只计算理论数
            1. 计算当前策略的剩余可开仓数
            2. 计算当前合约的剩余可开仓数
            3. 获取策略的单次开仓数
            取1,2,3的小者

        '''
        #print 'self.strategy.max_holding:%s' % (self.strategy.max_holding,)
        #print 'in calc_open_volume,self=%s,self.name=%s' % (str(self),self.instrument.name)
        logging.info(u'P_COV_1:计算头寸可开仓数,%s:Pos=%s' % (self.instrument.name,str(self)))
        self.re_calc()
        #剩余开仓总数 = 策略持仓限量 - 已开仓数，若小于0则为0
        remained = self.strategy.max_holding - self.locked_volume if self.strategy.max_holding > self.locked_volume else 0
        #print 'remained:%s' % (remained,)
        #inst_remained = self.instrument.calc_remained_volume() #因为机制原因，计算信号时没有办法确定同期锁定的数量. 故不再这里约束
        #print 'remained:%s,inst_remained:%s' % (remained,inst_remained)
        #if remained > inst_remained:
        #    remained = inst_remained
        #本次可开仓数 = 策略单次开仓数 和 剩余开仓总数 的小者
        #print 'self.strategy.open_volume:%s' % (self.strategy.open_volume,)
        can_open = self.strategy.open_volume if self.strategy.open_volume <=  remained else remained
        logging.info(u'P_COV_2:计算头寸可开仓数完成,可开数=%s,%s:Pos=%s' % (can_open,self.instrument.name,str(self)))
        return can_open

    def re_calc(self): #
        #print self.orders
        self.orders = [order for order in self.orders if not order.is_closed()]
        #print self.orders
        for mo in self.orders:
            logging.info(str(mo))
        self.opened_volume = sum([order.opened_volume for order in self.orders])
        self.locked_volume = sum([order.volume for order in self.orders])
        #print u'in re_calc:opened=%s,locked=%s,self.strategy.name=%s' % (self.opened_volume,self.locked_volume,type_name(self.strategy.opener))
        logging.info(u'P_RC_1:重算头寸，已开数=%s 策略总锁定数=%s,%s' % (self.opened_volume,self.locked_volume,str(self)))

    def add_order(self,order):
        self.orders.append(order)

    def get_locked_volume(self):    #返回已经占用数
        #print u'in get locked volume self=%s,self.name=%s' % (str(self),self.instrument.name)
        logging.info(u'P_GLV:获取头寸策略的总锁定数...,%s' % str(self))
        #总锁定数 = 开仓数 + 未成交的下单数
        self.re_calc()
        return self.locked_volume,self.opened_volume

    def __str__(self):
        return u'%s:%s:%x' % (self.instrument.name,type_name(self.strategy.opener),id(self))

##########
#策略和止损的公共基类
class Resumable(object):#可中间恢复
    #def save_parameters(self):  #保存参数. 应只允许有值参数，即字符串、数字
    #    return repr(self.__dict__)
    def save_parameters(self):  #保存参数. 只允许值参数，即字符串、数字
        parameters = []
        for key,value in self.__dict__.items():
            #print key,value,type(value)
            if type(value) == unicode:
                parameters.append(u"'%s':'%s'" % (key,value))   #这里不要多此一举，写成u"'%s':u'%s'",因为本来就是u的，如果再来一遍，就变成多搞了边encode('utf-8'),后面全乱
            elif type(value) == str:
                parameters.append(u"'%s':'%s'" % (key,value))
            elif type(value) == int:
                parameters.append(u"'%s':%d" % (key,value))
            elif type(value) == float:
                parameters.append(u"'%s':%s" % (key,value))
        return u'{%s}' % (','.join(parameters),)

    def load_parameters(self,parameters):  #重新装载参数
        self.__dict__.update(eval(parameters))
    

###突破类策略
###突破类策略以当前价为基准价，以一定额度的加价作为开仓限价以确保开仓，同时根据基准价来计算止损
'''
    check方法签名为(self,data,ctick)
    返回值为(触发标志,触发价格), 触发标志!=0时触发，触发价格==0时为当前价
'''

MAX_OVERFLOW = 60   #最大溢点，即开仓时加价跳数
VALID_LENGTH = 120  #行情跳数, 至少两分钟(视行情移动为准)

class BREAK(Resumable):    #策略标记
    pass

class LONG_BREAK(BREAK):    #多头突破策略
    direction = LONG
    def __init__(self,max_overflow=60,valid_length=VALID_LENGTH):
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'多头突破基类'

    def calc_target_price(self,base_price,tick_base):    #计算开单加价
        return base_price + tick_base * self.max_overflow

class SHORT_BREAK(BREAK):   #空头突破策略
    direction = SHORT
    def __init__(self,max_overflow=60,valid_length=VALID_LENGTH):
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
    def check(self,data,ctick):
        return (False,0)

class day_short_break(SHORT_BREAK):
    def check(self,data,ctick):
        return (False,0)


##止损类(平仓不允许钓鱼，必然直接平仓)
'''
    每个具体止损类必须实现三个方法
        __init__方法签名必须是(self,data,**kwargs),或者其它参数被fcustom化
        check方法签名为(self,ctick)
            必须返回(平仓标志, 基准价,止损变化标志)
            其中平仓标志:    False:不平仓, True:平仓
                         基准价为平仓基准价，将用于计算平仓限价
        calc_target_price(self,base_price,tick_base) #计算平仓限价, 其中tick_base是每跳幅度
'''

STOP_VALID_LENGTH = 2   #最好是1秒后就撤单, 以便及时追平

class STOPER(Resumable):    #离场类标记
    '''
        对于必须要实现断点恢复的stoper类，必须使用self.base_line和self.cur_stop作为判断标准
    '''
    def __init__(self,data,bline):
        self.cur_stop = 0
        self.data = data
        self.set_base_line(bline)

    def get_cur_stop(self):
        return self.cur_stop

    def set_cur_stop(self,cur_stop):
        self.cur_stop = cur_stop

    def get_base_line(self):
        return self.base_line

    def set_base_line(self,base_line):
        self.base_line = base_line

class LONG_STOPER(STOPER):
    def __init__(self,data,bline,max_overflow=120,valid_length=STOP_VALID_LENGTH):
        STOPER.__init__(self,data,bline)
        self.direction = SHORT
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'多头离场基类'

    def calc_target_price(self,base_price,tick_base):#计算多头平仓加价,
        return base_price - tick_base * self.max_overflow


class SHORT_STOPER(STOPER):
    def __init__(self,data,bline,max_overflow=120,valid_length=STOP_VALID_LENGTH):
        STOPER.__init__(self,data,bline)
        self.direction = LONG
        self.max_overflow = max_overflow    #溢点用于计算目标价
        self.valid_length = valid_length    #有效期用于计算撤单时间
        self.name = u'空头离场基类'

    def calc_target_price(self,base_price,tick_base):#计算空头平仓加价,
        return base_price + tick_base * self.max_overflow


class DATR_LONG_STOPER(LONG_STOPER):#日ATR多头止损
    def __init__(self,data,bline,rbase=0.12,rkeeper=0.2,rdrawdown = 0.4):
        '''data:行情对象
           bline: 价格基线
        '''
        LONG_STOPER.__init__(self,data,bline)
        self.thigh = bline
        self.ticks = 0
        self.name = u'多头日ATR止损,初始止损=%s,保本=%s,最大回撤=%s' % (rbase,rkeeper,rdrawdown)
        self.max_drawdown = int(data.atrd1[-1] * rdrawdown / XBASE + 0.5)
        self.keeper = int(data.atrd1[-1] * rkeeper / XBASE + 0.5)
        self.set_cur_stop(bline - int(data.atrd1[-1] * rbase / XBASE + 0.5))

    def check(self,tick):
        '''
            必须返回(平仓标志, 基准价,stop变化标志)
            基准价为0则为当前价
        '''
        stop_changed = False
        if tick.price < self.get_cur_stop():
            return (True,tick.price,stop_changed)
        if self.get_cur_stop()< self.get_base_line() and tick.price > self.get_base_line() + self.keeper:
            ##提升保本
            self.set_cur_stop(self.get_base_line())
            stop_changed = True
        if tick.price > self.thigh:
            self.thigh = tick.price
            if self.thigh - self.max_drawdown > self.get_cur_stop():
                self.set_cur_stop(self.thigh - self.max_drawdown)
                stop_changed = True
        return (False,self.get_base_line(),stop_changed)

class DATR_SHORT_STOPER(SHORT_STOPER):#日ATR空头止损
    def __init__(self,data,bline,rbase=0.12,rkeeper=0.2,rdrawdown = 0.4):
        SHORT_STOPER.__init__(self,data,bline)
        self.tlow = bline
        self.itime = len(self.data.sclose)  #time的索引，用于计算耗时
        self.name = u'空头日ATR止损,初始止损=%s,保本=%s,最大回撤=%s' % (rbase,rkeeper,rdrawdown)
        self.max_drawdown = int(data.atrd1[-1] * rdrawdown / XBASE + 0.5)
        self.keeper = int(data.atrd1[-1] * rkeeper / XBASE + 0.5)
        self.set_cur_stop(bline + int(data.atrd1[-1] * rbase / XBASE + 0.5))

    def check(self,tick):
        '''
            必须返回(平仓标志, 基准价,stop变化标志)
            基准价为0则为当前价
        '''
        stop_changed = False
        if tick.price > self.get_cur_stop():
            return (True,tick.price,stop_changed)
        if self.get_cur_stop()> self.get_base_line() and tick.price < self.get_base_line() - self.keeper:
            ##提升保本
            self.set_cur_stop(self.get_base_line())
            stop_changed = True
        if tick.price < self.tlow:
            self.tlow = tick.price
            if self.tlow + self.max_drawdown < self.get_cur_stop():
                self.set_cur_stop(self.tlow + self.max_drawdown)
                stop_changed = True
        return (False,self.get_base_line(),stop_changed)


datr_long_stoper_12 = fcustom(DATR_LONG_STOPER,rbase=0.12)
datr_short_stoper_12 = fcustom(DATR_SHORT_STOPER,rbase=0.12)

class LONG_MOVING_STOPER(LONG_STOPER):
    '''
        简化的移动跟踪止损, 达到快速提升止损和和逐步放开盈利端的平衡
    '''
    def __init__(self,data,bline,lost_base=100,max_drawdown=360,tstep=40,vstep=20,stime=1500):
        '''
           data:行情对象
           bline: 价格基线
        '''
        LONG_STOPER.__init__(self,data,bline)
        self.lost_base = lost_base
        self.ticks = 0
        self.set_cur_stop(bline - lost_base)
        self.stop0 = bline - lost_base
        self.name = u'多头移动止损,初始止损=%s,步长=%s/%s,最大回撤=%s' % (self.stop0,vstep,tstep,max_drawdown)
        self.thigh = bline
        self.stime = stime
        self.tstep = tstep
        self.vstep = vstep
        logging.info(self.name)

    def check(self,tick):
        '''
            必须返回(平仓标志, 基准价,stop变化标志)
            基准价为0则为当前价
        '''
        stop_changed = False
        if tick.price < self.get_cur_stop() or tick.time >= self.stime:
            return (True,tick.price,stop_changed)
        if tick.price > self.thigh:
            self.thigh = tick.price
            nstop = self.stop0 + (tick.price - self.base_line) / self.tstep * self.vstep
            if nstop > self.get_cur_stop():
                logging.info(u'移动平仓位置，新高点=%s,原平仓点=%s,现平仓点=%s' % (tick.price,self.get_cur_stop(),nstop))
                self.set_cur_stop(nstop)
                stop_changed = True
        return (False,self.get_base_line(),stop_changed)


class SHORT_MOVING_STOPER(SHORT_STOPER):#空头移动止损
    def __init__(self,data,bline,lost_base=100,max_drawdown=360,tstep=40,vstep=20,stime=1500):
        '''
           data:行情对象
           bline: 价格基线
        '''
        SHORT_STOPER.__init__(self,data,bline)
        self.lost_base = lost_base
        self.ticks = 0
        self.set_cur_stop(bline + lost_base)
        self.stop0 = bline + lost_base
        self.name = u'空头移动止损,初始止损=%s,步长=%s/%s,最大回撤=%s' % (self.stop0,vstep,tstep,max_drawdown)
        self.tlow = bline
        self.stime = stime
        self.vstep = vstep
        self.tstep = tstep
        logging.info(self.name)

    def check(self,tick):
        '''
            必须返回(平仓标志, 基准价,stop变化标志)
            基准价为0则为当前价
        '''
        stop_changed = False
        if tick.price > self.get_cur_stop() or tick.time >= self.stime:
            return (True,tick.price,stop_changed)
        if tick.price < self.tlow:
            self.tlow = tick.price
            nstop = self.stop0 - (self.base_line - tick.price) / self.tstep * self.vstep    
            #nstop = self.stop0 + (tick.price - self.base_line) / self.tstep * self.vstep    #不能这样，因为tick.price<self.base_line,所以会有四舍五入问题，-0.12舍入成-1
            if nstop < self.get_cur_stop():
                logging.info(u'移动平仓位置，新低点=%s,原平仓点=%s,现平仓点=%s,cur_price=%s,self.base_line=%s,stop0=%s' % (tick.price,self.get_cur_stop(),nstop,tick.price,self.base_line,self.stop0))
                logging.info(u'dp=%s,dp/tstep=%s' %(tick.price - self.base_line,(tick.price - self.base_line) / self.tstep))
                self.set_cur_stop(nstop)
                stop_changed = True
        return (False,self.get_base_line(),stop_changed)

if_lmv_stoper = fcustom(LONG_MOVING_STOPER,stime = 1500)
if_smv_stoper = fcustom(SHORT_MOVING_STOPER,stime = 1500)


class STRATEGY(object):#策略基类, 单纯包装
    def __init__(self,
                name,
                opener, #开仓类(注意，不是对象)
                closer, #平仓类(注意，不是对象)
                open_volume, #每次开仓手数   
                max_holding, #最大持仓手数 
            ):
        self.name = name
        self.opener = opener()  #单一策略可共享开仓对象
        self.closer = closer    #平仓对象必须用开仓时的上下文初始化
        self.open_volume = open_volume
        self.max_holding = max_holding
        self.direction = self.opener.direction

    def get_name(self):
        return u'%s_%s_%s_%s' % (self.opener.name,self.closer.name,self.open_volume,self.max_holding)
