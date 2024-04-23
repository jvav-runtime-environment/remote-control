# 远程控制

## 说明

* 使用`socket`实现客户端对服务端的控制，服务端和客户端需要运行在同一局域网内
* 服务端应置于Windows系统，客户端可以置于任何可以运行python代码的设备
* 程序目前实现了这些功能: 读取目录和文件，文件传输，cmd执行，创建目录，启动程序
* 这个是学socket时拿来练手的程序，仍有不少缺陷

> [!WARNING]
> 注意，这个程序的安全性 __没有__ 经过验证，建议不要在不安全的网络中使用
> (主要是流加密是自己写的简易实现方法，可能不安全)

## 介绍

* `chiper.py`是一个流加密模块，先将内容转换为base64，然后用密码作为随机数种子打乱字符

* `connection.py`是对socket的一层封装，主要用来一次性接收全部信息

* `filetransfer.py`是用来传输文件的模块，基于`connection.py`

* `processbar.py`是用来显示下载进度条的模块

* `client.py`是客户端程序

* `server_resolver.py`是用来解析和执行客户端命令的模块

* `server.py`是服务端程序

* `update.py`是更新时用来同步客户端的程序

## 使用

* 服务端依赖:
    - `server.py`
        - `server_resolver.py`
        - `connection.py`
        - `chiper.py`
        - `filetransfer.py`
        - `processbar.py`

* 客户端依赖:
    - `client.py`
        - `connection.py`
        - `chiper.py`
        - `filetransfer.py`
        - `processbar.py`

1. 将服务端和客户端依赖的文件置于同一文件夹下
2. 设置服务端和客户端的(客户端和服务端必须一样)
```python
    key = "<填写你的密码>"  # 连接密码
```
3. 启动服务端 (运行`server.py`和`startserver.bat`都可以)
4. 根据服务端控制台输出的IP填写客户端
```python
    ip = "<填写你的IP>"  # 连接IP
```
5. 启动客户端，等待连接

## 计划

- [ ] 加入数据包头验证
- [ ] 线程化

        

    
    

