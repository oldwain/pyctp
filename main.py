#-*- coding:utf-8 -*-

'''
主执行文件
    以后考虑把MAX_VOLUME和STRATEGY配置移到配置文件中
'''

from base import *
from strategy import *

#设定合约的策略

#[总最大持仓量,(策略名1，止损函数, 开仓方向，当次开仓数，最大持仓数),(策略名2，止损函数, 开仓方向,当次开仓数，最大持仓数)...]
STRATEGY = {
        'IF1103':[1,(ubreak,ufstop,LONG,1,1),(dbreak,dfstop,SHORT,1,1)]
        }


#####
import agent

def main():
    pass


if __name__=="__main__":
    main()
