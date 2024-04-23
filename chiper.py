import base64
import random


class Chiper:
    def __init__(self):
        self.__plain = list(
            b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890=+/"
        )
        self.__chiper = self.__plain.copy()
        self.__pwd = None

    def __update(self):
        random.shuffle(self.__chiper)

    def __reset(self):
        self.__chiper = self.__plain.copy()

    def set_pwd(self, pwd: str):
        self.__pwd = pwd

    def encrypt(self, text: bytes) -> bytes:
        b64_text = base64.encodebytes(text).replace(b"\n", b"")

        self.__reset()
        random.seed(self.__pwd)
        output_text = b""
        for i in b64_text:
            self.__update()
            output_text += self.__chiper[self.__plain.index(i)].to_bytes()

        return output_text

    def decrypt(self, text: bytes) -> bytes:
        self.__reset()
        random.seed(self.__pwd)
        output_text = b""
        for i in text:
            self.__update()
            output_text += self.__plain[self.__chiper.index(i)].to_bytes()

        return base64.decodebytes(output_text)
