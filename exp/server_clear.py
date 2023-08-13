import gzip

from utils import convert_code, build_message, parse_message, Serializer, Compression #, Message
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.messages.option import Option
import requests
import aiocoap
import enum
import cbor2
import noise
import struct
import socket
from itertools import cycle
from coapthon import defines
from noise.connection import NoiseConnection


if __name__ == "__main__":
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind(('localhost', 2000))
	connected = set()
	serializer = Serializer()

	while True:
		data, addr = s.recvfrom(2048)
		noise: NoiseConnection
		print(f'Accepted connection from {addr} with data - {len(data)} bytes')
		"""
		Before handshake:
		| UDP Datagram | Code = NN_HANDSHAKE          CoAP headers | CoAP Payload = Noise handshake |
		After handshake:
		| UDP Datagram | Code = NN_RQ/RS_NN_ENCRYPTED CoAP headers | Noise Encrypted (CoAP Payload) |
		Unencrypted
		| UDP Datagram | Code = Permitted COAP codes  CoAP headers | Noise Encrypted (CoAP Payload) |
		"""

		coap = serializer.deserialize(data)
		#print(data)
		#print(coap.pretty_print())
		if defines.Codes.LIST[coap.code] == defines.Codes.NN_HANDSHAKE:
			noise = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')
			noise.set_as_responder()
			noise.start_handshake()
			#Perform handshake. Break when finished
			for action in cycle(['receive', 'send']):
				if noise.handshake_finished:
					connected.add(addr)
					break
				elif action == 'send':
					ciphertext = noise.write_message()
					ser = build_message('NON', defines.Codes.NN_HANDSHAKE, ciphertext,
										"application/octet-stream", serialize = True)
					print(f"Sending response to {addr} - {len(ser)} bytes")
					s.sendto(ser, addr)
				elif action == 'receive':
					plaintext = noise.read_message(coap.payload)

		elif defines.Codes.LIST[coap.code] in (defines.Codes.NOISE_NN_RQ_ENCRYPTED, defines.Codes.NOISE_NN_RS_ENCRYPTED): # encryption enabled
			message = parse_message(data, noise)
			# print(gzip.decompress(message.payload))
			#text = cbor2.loads(noise.decrypt(coap.payload))
			if isinstance(message, Request):
				r = requests.get(f"https://api.lain-is.online/{message.uri_path}")
				ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, r.content, content_type = "application/octet-stream",
									serialize = True, compression = Compression.gzip, coder = noise)
			else:
				ser = build_message('NON', defines.Codes.NOISE_NN_RS_ENCRYPTED, message.payload.decode('utf-8').upper().encode('utf-8'),
								"application/octet-stream", serialize = True, compression = Compression.gzip, coder = noise)
			print(f"Sending response to {addr} - {len(ser)} bytes")
			s.sendto(ser, addr)
		else: # unencrypted payload
			ser = build_message('NON', defines.Codes.CONTENT,
								b'Unenc ' + coap.payload.encode('utf-8'), serialize = True)
			print(f"Sending response to {addr} - {len(ser)} bytes")
			s.sendto(ser, addr)
