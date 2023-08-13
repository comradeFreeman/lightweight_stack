# import socket
# import ssl
# from time import sleep
# from coap_tcp_tls_server import HOST as SERVER_HOST
# from coap_tcp_tls_server import PORT as SERVER_PORT
# import requests
#
# received, sent = 0, 0
# i = 1
# s = requests.Session()
# while i <= 150:
# 	r = s.get(f"https://127.0.0.1:2000/my/cool/api/json_{i}", verify=False)
# 	print(r.content)
# 	sleep(.1)
from datetime import datetime

import socket
import ssl
from time import sleep
from coap_tcp_tls_server import HOST as SERVER_HOST
from coap_tcp_tls_server import PORT as SERVER_PORT
from utils import convert_code, build_message, parse_message, Serializer, Compression
from coapthon import defines
import requests
from requests import Session

HOST = "127.0.0.1"
PORT = 2002

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

client = ssl.wrap_socket(client, keyfile="key.pem", certfile="cert.pem")

if __name__ == "__main__":
	client.bind((HOST, PORT))
	client.connect((SERVER_HOST, SERVER_PORT))

	received, sent = 0, 0
	i = 1
	while i <= 150:
		req = 	f"""
GET /my/cool/api/file/json_{i} HTTP/1.1
User-Agent: CoolPythonAgent/3.10.6
Accept: */*
Host: 127.0.0.1:2000
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
"""

		sent += client.send(req.encode('utf-8'))
		data = client.recv(1024)
		received += len(data)
		i+=1

# print(datetime.utcnow().strftime("%a, %d %b %G %T %Z"))

"""
GET /my/cool/api/file/json_1 HTTP/1.1
User-Agent: CoolPythonAgent/3.10.6
Accept: */*
Host: 127.0.0.1:1234
Accept-Encoding: gzip, deflate, br
Connection: keep-alive
"""

"""
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: Sun, 31 Mar 2019 13:59:30 GMT
Content-Length: 
Server: Nginx 1.18.0
Connection: keep-alive
Content-Encoding: gzip
Vary: Accept-Encoding

data
"""