import socket
import ssl
from time import sleep
from coap_tcp_tls_server import HOST as SERVER_HOST
from coap_tcp_tls_server import PORT as SERVER_PORT
from utils import convert_code, build_message, parse_message, Serializer, Compression
from coapthon import defines

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
		ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, content_type = "application/octet-stream",
							uri_path = f"/my/cool/api/file/json_{i}", serialize = True, compression = Compression.gzip)
		sent += client.send(ser)
		data = client.recv(1024)
		received += len(data)
		#coap = parse_message(data)
		i+=1


	print(f"\nReceived - {received} bytes\nSent - {sent} bytes")