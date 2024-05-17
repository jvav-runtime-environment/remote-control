import os
import logging as log
import json
import connection
import filetransfer


log.basicConfig(
    level=log.INFO,
    format="[%(asctime)s] [%(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    filemode="a",
    filename="log.txt",
)


def load_config():
    if os.path.exists("client_config.json"):
        conf = json.load(open("client_config.json", "r"))
    else:
        conf = {"key": "666", "ip": "loaclhost", "port": 23783}
        json.dump(conf, open("client_config.json", "w"))

    return conf


if not os.path.exists("./files"):
    os.mkdir("files")

conf = load_config()

ip = conf["ip"]  # 连接IP
key = conf["key"]  # 连接密码

connect = connection.Connection(port=conf["port"])
connect.set_key(key)
connect.connect(ip)

ft = filetransfer.FileTransferer(connect)


current_path = "d:"

# path操作函数---------


def format_path(path):
    return os.path.normpath(path).replace("\\", "/")


def is_abs(path):
    if path[1] == ":":
        return True
    else:
        return False


# 验证函数----------


def test_dir_exist(path):
    global current_path
    connect.send_msg({"type": "dir_exists", "path": format_path(path)})
    r = json.loads(connect.recv_msg())
    if r["success"]:
        return r["exists"]


def test_file_exist(filename):
    global current_path
    connect.send_msg(
        {"type": "file_exists", "path": format_path(current_path + "/" + filename)}
    )
    r = json.loads(connect.recv_msg())
    if r["success"]:
        return r["exists"]


# 命令处理函数----------


def cmd_type_msg(cmd):
    connect.send_msg({"type": "msg", "msg": " ".join(cmd[1:])})
    return json.loads(connect.recv_msg())


def cmd_type_cmd(cmd):
    connect.send_msg({"type": "cmd", "cmd": " ".join(cmd[1:])})
    return json.loads(connect.recv_msg())


def cmd_type_get_path(cmd):
    connect.send_msg({"type": "get_path", "current_path": current_path + "/"})
    return json.loads(connect.recv_msg())


def cmd_type_cd(cmd):
    global current_path
    if not cmd[1].isdigit():
        path = format_path(cmd[1])
    else:
        path = format_path(dirs[int(cmd[1])])

    if not is_abs(path):
        if test_dir_exist(current_path + "/" + path):
            current_path = format_path(current_path + "/" + path)
            return {"type": "cd", "success": True}
        else:
            return {"type": "cd", "success": False, "error": "目录不存在"}
    else:
        if test_dir_exist(path + "/"):
            current_path = path
            return {"type": "cd", "success": True}
        else:
            return {"type": "cd", "success": False, "error": "目录不存在"}


def cmd_type_recv_file(cmd):
    if not cmd[1].isdigit():
        filename = cmd[1]
    else:
        filename = files[int(cmd[1])]

    if not test_file_exist(filename):
        return {"type": "result_file_exists", "success": False, "error": "文件不存在"}

    connect.send_msg(
        {
            "type": "get_file",
            "path": format_path(current_path + "/" + filename),
            "using_chiper": False,
        }
    )

    ft.recv_file(path="./files")
    return json.loads(connect.recv_msg())


def cmd_type_send_file(cmd):
    if os.path.exists(cmd[1]):
        connect.send_msg(
            {
                "type": "recv_file",
                "path": current_path,
                "using_chiper": False,
            }
        )
        ft.send_file(cmd[1])
        return json.loads(connect.recv_msg())
    else:
        return {"type": "result_file_exists", "success": False, "error": "文件不存在"}


def cmd_type_back(cmd):
    global current_path
    current_path = format_path(current_path)

    l = current_path.split("/")
    if len(l) == 1:
        return {"type": "result_back", "success": True}
    else:
        l.pop()
        current_path = "/".join(l)
        return {"type": "result_back", "success": True}


def cmd_type_update(cmd):
    global current_path
    _temp = current_path
    current_path = "."

    files = [
        "chiper.py",
        "client.py",
        "connection.py",
        "filetransfer.py",
        "processbar.py",
        "update.py",
    ]

    for file in files:
        log.info(f"正在更新文件: {file}")
        result = cmd_type_recv_file(["get", file])
        if not result["success"]:
            log.error(f"更新文件 {file} 失败, {result['error']}")
            current_path = _temp
            return {"type": "result_update", "success": False, "error": "更新失败"}

    current_path = _temp
    return {"type": "result_update", "success": True}


def cmd_type_run(cmd):
    global current_path
    if not cmd[1].isdigit():
        filename = cmd[1]
    else:
        filename = files[int(cmd[1])]

    connect.send_msg(
        {"type": "run", "path": format_path(current_path + "/" + filename)}
    )
    return json.loads(connect.recv_msg())


def cmd_type_make_dir(cmd):
    global current_path
    connect.send_msg({"type": "make_dir", "path": current_path, "dirname": cmd[1]})
    return json.loads(connect.recv_msg())


dirs = []
files = []
while True:
    cmd = input(current_path + ">>> ")
    current_path = format_path(current_path)

    if cmd == "exit":
        break
    cmd = cmd.split()

    try:
        if cmd[0] == "msg":
            result = cmd_type_msg(cmd)

        elif cmd[0] == "cd":
            result = cmd_type_cd(cmd)
            result = cmd_type_get_path(cmd)

        elif cmd[0] == "ls":
            result = cmd_type_get_path(cmd)

        elif cmd[0] == "cmd":
            result = cmd_type_cmd(cmd)

        elif cmd[0] == "get":
            result = cmd_type_recv_file(cmd)

        elif cmd[0] == "send":
            result = cmd_type_send_file(cmd)

        elif cmd[0] == "back":
            result = cmd_type_back(cmd)
            result = cmd_type_get_path(cmd)

        elif cmd[0] == "update":
            result = cmd_type_update(cmd)

        elif cmd[0] == "run":
            result = cmd_type_run(cmd)

        elif cmd[0] == "mkd":
            result = cmd_type_make_dir(cmd)

        else:
            log.warning(f"未知命令: {cmd[0]}")
            continue

        log.info(f"接收返回值原始消息: {result}")

        if result["success"] == True:
            # print("执行成功")
            result_type = result["type"].replace("result_", "")

            if result_type == "get_path":
                dirs = result["dir"]
                files = result["files"]

                for i in range(len(dirs)):
                    print(f"|{i}\t| ", "<" + dirs[i] + ">")
                for i in range(len(files)):
                    print(f"|  {i}\t| ", files[i])

            elif result_type == "cmd":
                print(result["output"])

        else:
            print(f"执行失败, {result['error']}")
            log.error(
                f"命令 {result['type'].replace('result_', '')} 执行失败, {result['error']}"
            )

    except IndexError as e:
        log.warning(f"命令参数错误")
        continue

    except Exception as e:
        log.exception(e)
        log.error(f"未知错误: {e}")
        continue


connect.close()
