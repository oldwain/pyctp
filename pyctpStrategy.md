# 1,简介 #
pyctp分开定义开仓策略和平仓策略。


# 2.开仓策略 #
系统在初始化时，将调用所跟踪的开仓策略的dresume方法；同时每天行情初始化时，也会调用这一策略；
系统在每个tick到来之后，将会该策略的check()方法

## 2.1 dresume方法 ##
dresume方法用于每日交易前初始化数据，以及程序崩溃后重新设定指标现场；

## 2.2 check方法 ##
check方法会传递入两个参数，data和tick

### 2.2.1 data数据结构 ###
data是整个数据环境对象，包含多个实用数据：
```
cur_day: 有属性vopen/vclose/vhigh/vlow, 记录当日到当前tick为止的开盘/收盘/最高/最低价
iihigh/iilow: 当日高/低点的分钟序号
shigh/slow/sopen/sclose: 当日的分钟数据序列，分别对应高/低/开/收；
ma_7/ma_13/ma_20/ma_30: 预先计算的若干分钟收盘均线序列；以提高效率；以后会修改这个机制；
atr1/atr30/atrd1: 已完成的1分钟、30分钟、日的atr序列；
d1: 日周期数据序列；其中d1[IHIGH]/d1[ILOW]/d1[ICLOSE]/d1[IOPEN]分别是已完成日的数据；这一数据从合约数据目录的history.txt中读取；

```

### 2.2.2 ctick数据结构 ###
ctick是当前tick数据，包含如下属性：
```
min1:当前分钟
sec: 当前秒
msec: 当前毫秒
holding:持仓量
dvolume:当前总成交量
price:当前价格
high:截止目前最高价
low:截止目前最低价
bid_price:买价
bid_volume:买量
ask_price:卖价
ask_volume:卖量
date:当前日期
rev.time:当前时间，最小单位为秒
```