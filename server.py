import logging as log
import json
import server_resolver
import connection

log.basicConfig(
    level=log.DEBUG,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
)


key = "666"  # 连接密码
ip_blacklist = []

# 连接初始化
connect = connection.Connection()
connect.set_key(key)
connect.listen()

# 解析器初始化
resolver = server_resolver.Resolver(connect)

log.info(f"本机IP地址: {connect.ip}")

while True:
    try:
        log.info("等待连接...")
        addr = connect.accept()
        log.info(f"连接到IP: {addr[0]}, 端口: {addr[1]}")
        connect.apply_timeout(60)

        while True:
            # 阻止黑名单IP
            if addr[0] in ip_blacklist:
                connect.send_msg({"msg": "你啥玩意啊?"})
                log.info(f"{addr[0]}:{addr[1]} 的连接已被阻止")
                break

            # 接收消息
            msg = connect.recv_msg()

            # 解析消息
            if msg:
                log.info(
                    f"接收到客户端消息 {len(msg)} bytes, 原始信息: {json.loads(msg)}"
                )

                resolver.resolve(json.loads(msg))

            else:
                connect.close()
                log.info(f"{addr[0]}:{addr[1]} 的连接已断开")
                break

    except TimeoutError:
        log.info("连接超时")

    # 未处理错误
    except Exception as e:
        log.exception(e)
        log.error(f"未处理错误! : {e}")
