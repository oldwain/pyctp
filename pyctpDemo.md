首先请确保pyctp安装成功
程序运行目录须为pyctp主目录，并
import my.entry

# 1.行情记录 #
程序入口: my.entry.save\_demo()

基础配置采用demo\_base.ini；有效节为Base

行情记录设定了GF期货的两个行情链接，

为避免拥堵，请设定为开户期货公司的行情链接；

只需要到期货公司网站下载快期客户端，从其brokers.xml的Server->MarketData中可找到相应链接信息，从broker定义中可找到BrokerID；


# 2.模拟交易 #
程序入口: my.entry.trade\_mock()

基础配置采用demo\_base.ini；有效节为Base\_Mock；

请更改[SQ\_TRADER下]模拟交易链接的相关设定，包括investor\_id和passwd，设定为从上期申请的用户名和口令；

必要时，请修改相应的port和broker\_id；我申请到的第二个ID的broker\_id是4030

## 策略配置 ##
开仓策略为min\_long\_break,lgap, 都是演示性的；

平仓策略为day\_long\_stoper\_35，也是演示性的；

在strategy文件中有可实用的平仓策略；


# 3.真实交易 #
程序入口: my.entry.trade\_demo()

采用demo\_base.ini；有效节为Base\_Real；

请填充[REAL\_TRADER下]交易链接的相关设定；设置为真实交易配置信息；

