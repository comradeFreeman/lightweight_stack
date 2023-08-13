import socket

from noise.connection import NoiseConnection

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(5.0)
addr = ('localhost', 2000)
#sock.connect(('localhost', 2000))

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
sock.sendto(message, addr)
# Receive the data from the responder
received, addr = sock.recvfrom(2048)
# Feed the received data into noise
payload = proto.read_message(received)
# As of now, the handshake should be finished (as we are using NN pattern).
# Any further calls to write_message or read_message would raise NoiseHandshakeError exception.
# We can use encrypt/decrypt methods of NoiseConnection now for encryption and decryption of messages.
for text in ["Hello", "this is", "data", "chain", "using", "UDP", "and", "Noise"]:
	encrypted_message = proto.encrypt(text.encode("utf-8"))
	sock.sendto(encrypted_message, addr)
	ciphertext, addr = sock.recvfrom(2048)
	plaintext = proto.decrypt(ciphertext)
	print(plaintext)