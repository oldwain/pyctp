因为是完全DIY项目, 只建议C/PYTHON码农观摩使用; 非马农请勿自寻烦恼;

(一) 除项目源文件外,运行所需的其它设施:

1. python2.6

2. VC2008 express
> windows下的python2.6由vc2008编译而成,故python/c接口必须由其编译,同时对其有不明依赖.
> 仅安装vcredist包不足以成功使用相关接口pyd文件. 故须安装vc2008 express版本. 微软网站上可免费下载;

> 这是一个技术故障.理想情况下,应该不需安装VC2008,希望此间熟手点拨一二;

3. 配置文件
> base.ini:  需要用实际的模拟帐号或实盘帐号

> strategy.ini: 需要设定实际的行情服务器和所需保存行情的合约代码
> > (此处多次想主动判断存在的合约,而不需要硬编码合约代码,没时间做这个事情)


> strategy\_trade.ini: 设定实际的交易服务器,交易帐号以及交易策略配置

4. 策略文件
> mystrategy.py: 类似于strategy.py, 设计所需的具体策略;


(二) 项目执行:

1. ticks保存

> 在项目目录下,进入python26

> import agent

> agent.save\_raw2()

2. 交易执行(可模拟,查阅代码)

> import ctp\_mock

> ctp\_mock.comp\_real()