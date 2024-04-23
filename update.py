import pathlib

files = [
    "chiper.py",
    "client.py",
    "connection.py",
    "filetransfer.py",
    "processbar.py",
]

for file in files:
    file_path = pathlib.Path(file)
    file_path.replace("../" + file_path.name)
