#-*- coding:utf-8 -*-

from base import *
import ctp_mock
import agent


'''
    行情保存
    使用demo的配置文件
    其中demo_base_ini       配置相关的服务器地址和口令
        demo_strategy.ini   配置须保存ticks的合约
'''
def save_demo():
    return agent.save_raw(base_name='demo_base.ini',strategy_name='demo_strategy.ini')
