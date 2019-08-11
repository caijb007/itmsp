# coding: utf-8
# Author: Dunkle Qiu

from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
from urllib import quote, unquote


def pkcs5_pad(s):
    pad_size = 8 - len(s) % 8
    return s + pad_size * chr(pad_size)


def pkcs5_unpad(s):
    pad_size = ord(s[-1])
    if pad_size <= 8 and s[-pad_size:] == pad_size * s[-1]:
        return s[:-pad_size]
    else:
        raise Exception(u"Unpadding Failed!")


def des3_encrypt(data, key):
    """
    3DES加密, data为未填充字符串，填充算法为Pkcs#5
    @param data: plain data
    @type data: str
    @param key: 24 bytes key string
    @type key: str
    @return: encrypted string
    """
    assert len(key) == 24, u"用于3DES加密的key必须为24字节定长字符串"
    pad_data = pkcs5_pad(data)
    cipher = DES3.new(key, DES3.MODE_ECB)
    enc_data = cipher.encrypt(pad_data)
    return enc_data


def des3_decrypt(enc_data, key):
    """
    3DES解密，填充算法为Pkcs#5
    @param enc_data: encrypted string
    @type enc_data: str
    @param key: 24 bytes key string
    @type key: str
    @return: plain data
    """
    assert len(key) == 24, u"用于3DES解密的key必须为24字节定长字符串"
    cipher = DES3.new(key, DES3.MODE_ECB)
    pad_data = cipher.decrypt(enc_data)
    data = pkcs5_unpad(pad_data)
    return data
