# 1.安装python2.6 #
因接口pyd是用vc2008express链接python2.6编译,故须安装python2.6

## 1.1 下载安装包 ##
[python2.6](http://www.python.org/ftp/python/2.6.6/python-2.6.6.msi)

## 1.2 安装 ##
建议安装在D:\python26目录下, 以下默认

## 1.3 设定环境变量: ##

我的电脑-->属性-->高级-->环境变量

**添加:**

PYTHON\_HOME 值为安装目录,即 d:\python26

**修改 Path**

在Path末尾添加: ;%PYTHON\_HOME%\


## 1.4 测试安装成功 ##
打开dos窗口, 输入 python
若回应为
```
Python 2.6.6 (r266:84297, Aug 24 2010, 18:46:32) [MSC v.1500 32 bit (Intel)] on

win32

Type "help", "copyright", "credits" or "license" for more information.

>>>
```

则表示python2.6安装成功


# 2. 安装vc2008 express #
目前必须,希望有同道能搞定这个再分发的依赖
## 2.1 下载软件包 ##
点击下载: [VC2008Express](http://www.microsoft.com/visualstudio/en-us/products/2008-editions/express)

选择 **Visual C++ 2008 Express Edition with SP1** 简体中文版

下载后的文件为vcsetup.exe

## 2.2 安装 ##
点击下载的vcsetup.exe,安装vc2008 express

在选择要安装的可选产品页面时, 去掉默认选中的sliverlight和sqlserver

此处安装需要较长时间,视本机操作系统版本和网络速度而定

裸XP系统，需要安装1.1G.



# 3. 安装pyctp #
## 3.1 下载 ##
在[pyctp0.1a](http://code.google.com/p/pyctp/downloads/list)中，下载pyctp\_0.1a.zip

## 3.2 安装 ##
将pyctp\_0.1a.zip解压到d:\盘；完成后，d:\pyctp下即为相应程序

将d:\pyctp\bin目录下4个文件(不含子目录)复制到 C:\Python26\Lib\site-packages

## 3.3 设定当前python的默认语言 ##

查看D:\Python26\Lib\site-packages下是否存在文件sitecustomize.py

若不存在，则将pyctp安装目录的bin\site-packages下的sitecustomize.py文件复制到D:\Python26\Lib\site-packages

若存在sitecustomize.py，则将
```
import sys
sys.setdefaultencoding('gbk')
```

复制到该文件中.


## 3.4 验证安装 ##
打开dos窗口, 输入 python, 在随后的提示行中输入:

`import _ctp_Md`

若未有任何报错信息，则安装成功