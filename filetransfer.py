from io import BufferedReader
import json
import pathlib
import connection
import logging as log
import processbar

block_size = 8192


class FileTransferer:
    def __init__(self, conn: connection.Connection):
        self.conn = conn
        self.using_chiper = False

    def enable_chiper(self, b: bool):
        # 设置加密是否启用
        self.using_chiper = b

    def send_file(self, filename: str):
        # 发送文件
        filepath = pathlib.Path(filename)
        filesize = filepath.stat().st_size
        base_filename = filepath.name

        self.conn.send_msg(  # 发送文件信息
            json.dumps({"filesize": filesize, "filename": base_filename}),
            self.using_chiper,
        )
        log.info(f"[文件传输]: 准备发送, 文件大小: {filesize}")

        num = 0  # 用于判断前后数据包编号是否相等
        bar = processbar.ProgressBar(total=filesize, info=f"正在发送{filename}")
        with open(filename, "rb") as f:
            while True:
                finished, l_num = self.send_block(f)
                if finished:
                    break

                if l_num != num:  # 数据包编号不相等，说明前后数据包不同
                    bar.work(block_size)
                    num = l_num

    def recv_file(self, filename=None, path=""):
        # 接收文件
        _msg = json.loads(self.conn.recv_msg(self.using_chiper))

        # 文件信息
        filesize = _msg["filesize"]
        if not filename:
            filename = _msg["filename"]
        log.info(f"[文件传输]: 准备接收, 文件大小: {filesize}")

        num = 1  # 数据包编号
        retries = 5  # 重试次数
        num_total = filesize // block_size + (
            1 if filesize % block_size else 0
        )  # 文件总块数
        bar = processbar.ProgressBar(
            total=filesize, info=f"正在接收{pathlib.Path(filename).name}"
        )
        with open(path + "/" + filename, "wb") as f:
            while True:
                if retries == 0:
                    break

                # 接收, 5次重试
                try:
                    data = self.get_block(num)
                    retries = 5
                except TimeoutError:
                    retries -= 1
                    continue

                f.write(data)
                bar.work(len(data))

                if num == num_total:
                    break

                num += 1

        # 通知发送完成
        self.get_block(0)

    def get_block(self, block_num: int):
        # 请求块
        self.conn.send_msg(json.dumps({"block_num": block_num}), self.using_chiper)
        return self.conn.recv_raw_msg(self.using_chiper)

    def send_block(self, file: BufferedReader):
        # 发送块
        num = json.loads(self.conn.recv_msg(self.using_chiper))["block_num"]

        if num != 0:
            file.seek((num - 1) * block_size)
            self.conn.send_raw_msg(file.read(block_size), self.using_chiper)
            return [False, num]
        else:
            # num=0说明发送完成
            self.conn.send_raw_msg(b"0", self.using_chiper)
            return [True, num]
