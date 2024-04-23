import socket
import logging as log
import json
import chiper


class Connection:
    def __init__(self, port=23783):
        # 连接初始化
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.socket = socket.socket()
        self.conn = None

        # 加密初始化
        self.chiper = chiper.Chiper()
        self.chiper_enabled = False

    def listen(self, n=1):
        # 服务端初始化
        self.socket.bind((self.ip, self.port))
        self.socket.listen(n)

    def accept(self):
        # 服务端接受连接
        self.conn, addr = self.socket.accept()
        return addr

    def connect(self, ip):
        # 客户端创建连接
        self.socket.connect((ip, self.port))
        self.conn = self.socket

    def apply_timeout(self, timeout):
        # 设置超时
        self.conn.settimeout(timeout)

    def remove_timeout(self):
        # 移除超时
        self.conn.settimeout(None)

    def set_key(self, key):
        # 设置加密密码
        self.chiper.set_pwd(key)
        self.chiper_enabled = True

    def __generat_msg(self, msg: dict, using_chiper=True):
        # 生成消息
        # 数据包结构: 8字节长度 + json数据
        if self.chiper_enabled and using_chiper:
            msg = self.chiper.encrypt(json.dumps(msg).encode())
        else:
            msg = json.dumps(msg).encode()

        msg_len = len(msg)
        return msg_len.to_bytes(8) + msg

    def send_msg(self, msg: str | dict, using_chiper=True):
        # 发送消息
        if isinstance(msg, str):
            self.conn.send(self.__generat_msg(json.loads(msg), using_chiper))
        elif isinstance(msg, dict):
            self.conn.send(self.__generat_msg(msg, using_chiper))
        else:
            raise TypeError(f"消息类型错误, 不支持的消息类型: {type(msg)}")

    def send_raw_msg(self, msg: bytes, using_chiper=True):
        # 发送原始消息
        # 数据包结构: 8字节长度 + 数据
        if self.chiper_enabled and using_chiper:
            msg = self.chiper.encrypt(msg)
        msg_len = len(msg)

        self.conn.send(msg_len.to_bytes(8) + msg)

    def recvall(self, default_timeout=5):
        # 根据数据大小尝试接收全部数据
        msg_len = int.from_bytes(self.conn.recv(8))  # 首位8字节为数据包大小

        msg = b""
        _timeout = self.conn.gettimeout()
        self.conn.settimeout(default_timeout)
        while msg_len > 0:  # 接收全部数据
            recv = self.conn.recv(1024 if msg_len > 1024 else msg_len)
            if recv:
                # 判断接收内容不为空
                msg += recv
                msg_len -= len(recv)
            else:
                # 如果为空则连接已断开
                log.error("接收过程中断!")
                return None

        self.conn.settimeout(_timeout)  # 恢复超时设置
        return msg

    def recv_msg(self, using_chiper=True):
        # 接收消息
        msg = self.recvall()

        if self.chiper_enabled and using_chiper:
            msg = self.chiper.decrypt(msg)

        # 判断解密是否正确
        try:
            return msg.decode()
        except UnicodeDecodeError as e:
            log.warning(f"解密错误, 明文解码错误: {e}")
            return None

    def recv_raw_msg(self, using_chiper=True):
        # 接收原始消息
        msg = self.recvall()

        if self.chiper_enabled and using_chiper:
            msg = self.chiper.decrypt(msg)

        return msg

    def close(self):
        # 关闭连接
        self.conn.close()
