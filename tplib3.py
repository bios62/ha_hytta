#
# TP-Link Wi-Fi Smart Plug Protocol Client
# For use with TP-Link HS-100 or HS-110
#
# by Lubomir Stroetmann
# Copyright 2016 softScheck GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# 14/8-2023 modified to work with Python3, changed code to more strick byte manipulation

import socket
import json
import sys
import argparse
from struct import pack
from pprint import pprint

version = 0.3


# Check if hostname is valid
def validHostname(hostname):
    try:
        socket.gethostbyname(hostname)
    except socket.error:
        parser.error("Invalid hostname.")
    return hostname


# Predefined Smart Plug Commands
# For a full list of commands, consult tplink_commands.txt


# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
def encrypt(string):
    key = 171
    result = bytearray(pack(">I", len(string)))
    for i in string:
        a = key ^ ord(i)
        key = a
        result.extend(a.to_bytes(1, byteorder="big"))
    return bytes(result)


def decrypt(string_of_bytes):
    key = 171
    result = ""
    string = string_of_bytes.decode("iso-8859-1")
    for i in string:
        a = key ^ ord(i)
        key = ord(i)
        result += chr(a)
    return result


"""
# Old code
def encrypt(string):
	key = 171
	result = pack('>I', len(string))
	for i in string:
		a = key ^ ord(i)
		key = a
		result += chr(a)
	return result

def decrypt(string):
	key = 171
	result = ""
	for i in string:
		a = key ^ ord(i)
		key = ord(i)
		result += chr(a)
	return result
"""


def do_tplink(ip, cmd, port, useJson=True):
    try:
        sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_tcp.connect((ip, port))
        sock_tcp.send(encrypt(cmd))
        data = sock_tcp.recv(2048)
        if useJson:
            result = json.loads(decrypt(data[4:]))
        else:
            result = json.dumps(json.loads(decrypt(data[4:])), sort_keys=True, indent=2)
        sock_tcp.close()
        return result
    except socket.error:
        quit("Cound not connect to host " + ip + ":" + str(port))
