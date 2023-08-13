import socket
import ssl
from utils import convert_code, build_message, parse_message, Serializer, Compression
from coapthon.messages.request import Request
from os import path
import json
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
			message = parse_message(data)
			if isinstance(message, Request) and "file" in message.uri_path and \
					path.exists(path.join(path.dirname(path.realpath(__file__)), f"data/{message.uri_path.split('/')[-1]}")):
				file = message.uri_path.split('/')[-1]
				data = json.load(open(f"data/{file}", 'r'))
				ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, json.dumps(data, separators=(',', ':')),
									content_type = "application/octet-stream",	serialize = True, compression = Compression.gzip)
				connection.send(ser)
			else:
				print(f"Received: {data.decode('utf-8')}")
				connection.send(data.decode('utf-8').upper().encode('utf-8'))