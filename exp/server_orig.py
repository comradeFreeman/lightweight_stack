from coapthon.server.coap import CoAP
import cbor2
import noise

# # Create a CoAP server object.
# server = CoAP()


import socket
from itertools import cycle

from noise.connection import NoiseConnection

if __name__ == '__main__':
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('localhost', 2000))
	s.settimeout(50.0)
	#s.listen(1)

	#data, addr = s.recvfrom(1024) #s.accept()
	#print('Accepted connection from', addr)

	noise = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')
	noise.set_as_responder()
	noise.start_handshake()
	print("1")
	#Perform handshake. Break when finished
	for action in cycle(['receive', 'send']):
		if noise.handshake_finished:
			print("2")
			break
		elif action == 'send':
			print("3")
			ciphertext = noise.write_message()
			s.sendto(ciphertext, addr)
		elif action == 'receive':
			print("4")
			message, addr = s.recvfrom(2048)
			print('Accepted connection from', addr)
			plaintext = noise.read_message(message)

	# Endless loop "echoing" received data
	while True:
		print("5")
		data, addr = s.recvfrom(2048)
		if not data:
			break
		received = noise.decrypt(data)
		s.sendto(noise.encrypt(received), addr)