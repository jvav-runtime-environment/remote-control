import logging as log
import os
import subprocess
import time
import connection
import filetransfer


class Resolver:
    def __init__(self, conn: connection.Connection):
        self.msg = ""
        self.conn = conn
        self.default_return_msg = {"type": "result", "success": True}
        self.return_msg = self.default_return_msg

        self.filetransferer = filetransfer.FileTransferer(self.conn)

    def set_return_msg(self, msg: dict):
        self.return_msg = msg

    def finish_up(self):
        self.conn.send_msg(self.return_msg)

    def resolve(self, msg: dict):
        self.msg = msg
        self.return_msg = self.default_return_msg

        try:
            if msg["type"] == "msg":
                self.msg_type_msg()

            elif msg["type"] == "get_path":
                self.msg_type_get_path()

            elif msg["type"] == "cmd":
                self.msg_type_cmd()

            elif msg["type"] == "get_file":
                self.msg_type_get_file()

            elif msg["type"] == "recv_file":
                self.msg_type_recv_file()

            elif msg["type"] == "file_exists":
                self.msg_type_file_exists()

            elif msg["type"] == "dir_exists":
                self.msg_type_dir_exists()

            elif msg["type"] == "run":
                self.msg_type_run()

            elif msg["type"] == "make_dir":
                self.msg_type_make_dir()

            else:
                log.warning("[解析器]: 消息命令类型不存在: {}".format(msg["type"]))
                self.set_return_msg(
                    {
                        "type": "result",
                        "success": False,
                        "error": "消息命令类型不存在: {}".format(msg["type"]),
                    }
                )

        except KeyError as e:
            log.warning(f"[解析器]: 消息键值缺失, 缺失键值: {e.args[0]}")
            self.set_return_msg(
                {
                    "type": "result",
                    "success": False,
                    "error": f"消息键值缺失, 缺失键值: {e.args[0]}",
                }
            )

        except Exception as e:
            log.error(f"[解析器]: 未知错误: {e}")
            self.set_return_msg(
                {
                    "type": "result",
                    "success": False,
                    "error": f"未知错误: {e}",
                }
            )

        self.finish_up()

    def msg_type_msg(self):
        # 格式: {'type': 'msg', 'msg': '...'}
        log.info("[解析器]: 接收到消息: " + self.msg["msg"])
        self.set_return_msg({"type": "result_msg", "success": True})

    def msg_type_file_exists(self):
        # 格式: {'type': 'file_exists', 'path': '...'}
        path = self.msg["path"]
        log.info(f"[解析器]: 客户端请求检查路径存在: {path}")

        if os.path.isfile(path):
            self.set_return_msg(
                {
                    "type": "result_file_exists",
                    "success": True,
                    "exists": True,
                }
            )

        else:
            self.set_return_msg(
                {
                    "type": "result_file_exists",
                    "success": True,
                    "exists": False,
                }
            )

    def msg_type_dir_exists(self):
        # 格式: {'type': 'dir_exists', 'path': '...'}
        path = self.msg["path"]
        log.info(f"[解析器]: 客户端请求检查路径存在: {path}")

        if os.path.isdir(path):
            self.set_return_msg(
                {
                    "type": "result_dir_exists",
                    "success": True,
                    "exists": True,
                }
            )

        else:
            self.set_return_msg(
                {
                    "type": "result_dir_exists",
                    "success": True,
                    "exists": False,
                }
            )

    def msg_type_get_path(self):
        # 格式: {'type': 'get_path', 'current_path': '...'}
        path = self.msg["current_path"]

        if os.path.isdir(path):
            for dir, dirs, files in os.walk(path):
                break

            self.set_return_msg(
                {
                    "type": "result_get_path",
                    "success": True,
                    "dir": dirs,
                    "files": files,
                }
            )

            log.info(
                f"[解析器]: 客户端请求从 {path} 的目录\n文件夹: {dirs}\n文件名: {files}"
            )

        else:
            log.warning(
                "[解析器]: 客户端提供了一个不存在的路径: {}".format(
                    self.msg["current_path"]
                )
            )
            self.set_return_msg(
                {
                    "type": "result_get_dir",
                    "success": False,
                    "error": "提供的路径不存在",
                }
            )

    def msg_type_cmd(self):
        # 格式: {'type': 'cmd', 'cmd': '...'}
        cmd = self.msg["cmd"]
        log.info(f"[解析器]: 客户端传入命令: {cmd}")

        try:
            console = subprocess.run(
                cmd, capture_output=True, shell=True, encoding="gbk", timeout=10
            )

            log.info(f"[解析器]: 命令执行结果: \n{console.stdout}")
            self.set_return_msg(
                {"type": "result_cmd", "success": True, "output": console.stdout}
            )

        except TimeoutError as e:
            log.warning(f"[解析器]: 运行命令超时, {e}")
            self.set_return_msg(
                {"type": "result_cmd", "success": False, "error": f"运行命令超时, {e}"}
            )

    def msg_type_get_file(self):
        # 格式: {'type': 'get_file', 'path': '...', 'using_chiper': True|False}
        path = self.msg["path"]
        using_chiper = self.msg["using_chiper"]
        self.filetransferer.enable_chiper(using_chiper)
        log.info(f"[解析器]: 客户端请求从 {path} 获取文件, 使用加密: {using_chiper}")

        try:
            self.filetransferer.send_file(path)
            self.set_return_msg({"type": "result_get_file", "success": True})
            log.info(f"[解析器]: 文件传输成功")

        except FileNotFoundError as e:
            log.warning(f"[解析器]: 文件不存在, {e}")
            self.set_return_msg(
                {
                    "type": "result_get_file",
                    "success": False,
                    "error": f"文件不存在, {e}",
                }
            )

        except Exception as e:
            log.error(f"[解析器]: 文件传输失败, {e}")
            self.set_return_msg(
                {
                    "type": "result_get_file",
                    "success": False,
                    "error": f"未知错误, {e}",
                }
            )

    def msg_type_recv_file(self):
        # 格式: {'type': 'recv_file', 'path': '...', 'using_chiper': True|False}
        path = self.msg["path"]
        using_chiper = self.msg["using_chiper"]
        self.filetransferer.enable_chiper(using_chiper)
        log.info(f"[解析器]: 客户端传入文件, {path}, 使用加密: {using_chiper}")

        try:
            self.filetransferer.recv_file(path=path + "/")
            self.set_return_msg({"type": "result_recv_file", "success": True})
            log.info(f"[解析器]: 文件接收成功")
        except Exception as e:
            log.error(f"[解析器]: 文件接收失败, {e}")
            self.set_return_msg(
                {
                    "type": "result_recv_file",
                    "success": False,
                    "error": f"未知错误, {e}",
                }
            )

    def msg_type_run(self):
        # 格式: {'type': 'run', 'path': '...'}
        path = self.msg["path"]
        log.info(f"[解析器]: 客户端请求运行 {path}")

        if os.path.isfile(path):
            subprocess.Popen(path)
            self.set_return_msg({"type": "result_run", "success": True})
            log.info(f"[解析器]: 运行成功")
        else:
            log.warning(f"[解析器]: 文件不存在, {path}")
            self.set_return_msg(
                {
                    "type": "result_run",
                    "success": False,
                    "error": f"文件不存在, {path}",
                }
            )

    def msg_type_make_dir(self):
        # 格式: {'type': 'make_dir', 'path': '...', 'dirname': '...'}
        path = self.msg["path"]
        dirname = self.msg["dirname"]
        log.info(f"[解析器]: 客户端请求在 {path} 创建目录 {dirname}")

        os.makedirs(path + "/" + dirname)
        self.set_return_msg({"type": "result_make_dir", "success": True})
        log.info(f"[解析器]: 目录创建成功")
