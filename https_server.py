# from http.server import BaseHTTPRequestHandler
# from https.server import HTTPSServer, generate_cert
# from os import path
# import json
#
# class CustomRequestHandler(BaseHTTPRequestHandler):
# 	def do_GET(self):
# 		print("1")
# 		file = self.path.split('/')[-1]
# 		data = json.load(open(f"data/{file}", 'r'))
# 		to_send = json.dumps(data, separators=(',', ':')).encode('utf-8')
#
# 		self.protocol_version = "HTTP/1.1"
# 		print("2")
# 		self.send_response(200)
# 		self.send_header("Content-Length", len(to_send))
# 		self.end_headers()
# 		self.wfile.write(to_send)
# 		print("3")
# 		return
#
# #cert_path = (path.join(path.dirname(path.realpath(__file__)), "cert.key"), path.join(path.dirname(path.realpath(__file__)), "cert.pem"))
# server = ("127.0.0.1", 2000)
#
# httpd = HTTPSServer(path.join(path.dirname(path.realpath(__file__)), "key.pem"),
# 					path.join(path.dirname(path.realpath(__file__)), "cert.pem"), server, CustomRequestHandler)
# httpd.serve_forever()

import socket
import ssl
from utils import convert_code, build_message, parse_message, Serializer, Compression
from coapthon.messages.request import Request
from os import path
import json
import gzip
from datetime import datetime
from coapthon import defines

HOST = "127.0.0.1"
PORT = 2000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server = ssl.wrap_socket(
	server, server_side=True, keyfile="key.pem", certfile="cert.pem"
)

if __name__ == "__main__":
	server.bind((HOST, PORT))
	server.listen(0)

	while True:
		connection, client_address = server.accept()
		while True:
			data = connection.recv(1024)
			if not data:
				break
			message = data.decode('utf-8').split('\n')
			method, uri_path, protocol = message[1].split()
			if isinstance(message, Request) and "file" in uri_path and \
					path.exists(path.join(path.dirname(path.realpath(__file__)), f"data/{uri_path.split('/')[-1]}")):
				file = uri_path.split('/')[-1]
				data = json.load(open(f"data/{file}", 'r'))
				gzipped_data = gzip.compress(json.dumps(data, separators=(',', ':')).encode('utf-8'), 9)
				resp =  f"""
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Date: {datetime.utcnow().strftime("%a, %d %b %G %T %Z")}
Content-Length: {len(gzipped_data)}
Server: Nginx 1.18.0
Connection: keep-alive
Content-Encoding: gzip
Vary: Accept-Encoding
						
"""
				connection.send(resp.encode('utf-8') + gzipped_data)
			else:
				print(f"Received: {data.decode('utf-8')}")
				connection.send(data.decode('utf-8').upper().encode('utf-8'))