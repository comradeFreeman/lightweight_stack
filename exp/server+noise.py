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
	#s.settimeout(50.0)
	#s.listen(1)
	connected = set()
	#data, addr = s.recvfrom(1024) #s.accept()
	#print('Accepted connection from', addr)

	while True:
		message, addr = s.recvfrom(2048)
		noise: NoiseConnection
		print('Accepted connection from', addr)
		if addr in connected:
			if not message:
				break
			received = noise.decrypt(message)
			s.sendto(noise.encrypt(received.upper()), addr)
		else:
			noise = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')
			noise.set_as_responder()
			noise.start_handshake()
			#Perform handshake. Break when finished
			for action in cycle(['receive', 'send']):
				if noise.handshake_finished:
					connected.add(addr)
					break
				elif action == 'send':
					print("2")
					ciphertext = noise.write_message()
					s.sendto(ciphertext, addr)
				elif action == 'receive':
					print("3")
					plaintext = noise.read_message(message)
		print("4")
		# if skip:
		# 	skip = False
		# 	continue
		print("6")
		# Endless loop "echoing" received data
		# data, addr = s.recvfrom(2048)
