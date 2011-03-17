# -*- coding: utf8 -*-

'''
    策略
    包括紧盯的合约
    目前支持手工设定标的合约，有时间时自动盘前判断主力合约

'''

##策略函数
'''
每个策略函数必须返回(开仓标志, 基准价)
其中开仓标志:
    0:不开仓
    1:开空
    -1:开多
基准价为设置止损的基准价
'''

def ubreak(data,tick):
    return (0,0)

def dbreak(data,tick):
    return (0,0)

##止损函数
'''
止损函数的参数是:
    data:数据集合
    tick:当前行情
    bline: 基准价
返回:
    0: 持仓不动
    1: 止损

'''
def ufstop(data,tick,bline):
    return 0

def dfstop(data,tick,bline):
    return 0
