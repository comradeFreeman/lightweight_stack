import socket

import cbor2
from noise.connection import NoiseConnection
from coapthon.messages.message import Message
from utils import convert_code, build_message, parse_message, Serializer, Compression
from coapthon import defines
from time import sleep
import requests


serializer = Serializer()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
addr = ('localhost', 2000)

# Create instance of NoiseConnection, set up to use NN handshake pattern, Curve25519 for
# elliptic curve keypair, ChaCha20Poly1305 as cipher function and SHA256 for hashing.
proto = NoiseConnection.from_name(b'Noise_NN_25519_ChaChaPoly_SHA256')

# Set role in this connection as initiator
proto.set_as_initiator()
# Enter handshake mode
proto.start_handshake()

# Perform handshake - as we are the initiator, we need to generate first data.
# We don't provide any payload (although we could, but it would be cleartext for this pattern).
message = proto.write_message()
# Send the data to the responder - you may simply use sockets or any other way
# to exchange bytes between communicating parties.
ser = build_message('NON', defines.Codes.NN_HANDSHAKE, message,
					"application/octet-stream", serialize=True)
sock.sendto(ser, addr)
# Receive the data from the responder
data, addr = sock.recvfrom(2048)
hs = serializer.deserialize(data)
# Feed the received data into noise
payload = proto.read_message(hs.payload)
# As of now, the handshake should be finished (as we are using NN pattern).
# Any further calls to write_message or read_message would raise NoiseHandshakeError exception.
# We can use encrypt/decrypt methods of NoiseConnection now for encryption and decryption of messages.

# for text in ["Hello", "this is", "data", "chain", "using", "UDP", "and", "Noise"]:
# 	# ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, proto.encrypt(cbor2.dumps(text.encode("utf-8"))),
# 	# 				  "application/octet-stream", serialize = True)
# 	ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, text, "application/octet-stream",
# 						serialize = True, compression = Compression.gzip, coder = proto)
# 	sock.sendto(ser, addr)
# 	data, addr = sock.recvfrom(2048)
# 	coap = parse_message(data, proto) #serializer.deserialize(data)
# 	plaintext = coap.payload.decode('utf-8')# cbor2.loads(proto.decrypt(coap.payload)).decode('utf-8')
# 	print(plaintext)
#
# for text in ["okay", "let's", "try", "unencrypted", "data"]:
# 	ser = build_message('NON', defines.Codes.POST, text, serialize = True)
# 	sock.sendto(ser, addr)
# 	data, addr = sock.recvfrom(2048)
# 	hs = serializer.deserialize(data)
# 	print(hs.payload)

# i = 0
# while i < 10:
# 	#r = requests.get("https://api.lain-is.online/v1/lmg/network/test")
# 	ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, content_type = "application/octet-stream",
# 						uri_path = "/v1/lmg/network/test", serialize = True, compression = Compression.gzip, coder = proto)
# 	sock.sendto(ser, addr)
# 	data, addr = sock.recvfrom(2048)
# 	coap = parse_message(data, proto) #serializer.deserialize(data)
# 	#plaintext = cbor2.loads(proto.decrypt(coap.payload)).decode('utf-8')
# 	print(coap.payload.decode('utf-8'))
# 	sleep(2)
# 	i += 1

received, sent = 0, 0
i = 1
while i <= 150:
	ser = build_message('NON', defines.Codes.NOISE_NN_RQ_ENCRYPTED, content_type = "application/octet-stream",
						uri_path = f"/my/cool/api/file/json_{i}", serialize = True, coder = proto) #, compression = Compression.gzip)
	sent += sock.sendto(ser, addr)

	data, addr = sock.recvfrom(2048)
	received += len(data)
	coap = parse_message(data, proto)
	#print(coap.payload.decode('utf-8'))
	i += 1

print(f"\nReceived - {received} bytes\nSent - {sent} bytes")