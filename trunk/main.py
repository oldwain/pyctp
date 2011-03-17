#-*- coding:utf-8 -*-

'''
主执行文件
    以后考虑把MAX_VOLUME和STRATEGY配置移到配置文件中
'''

from strategy import *

####配置
#每个合约的最大持仓量
MAX_VOLUME = {
        'IF1103':1,
        }

#每个合约所应用的策略(策略名，止损函数, 开仓数)
STRATEGY = {
        'IF1103':[(ubreak,ufstop,1),(dbreak,dfstop,1)]
        }


#####
import agent

def main():
    pass


if __name__=="__main__":
    main()
