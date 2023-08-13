from coapthon import defines
defines.Codes.NN_HANDSHAKE = defines.CodeItem(250, 'NN Handshake')
defines.Codes.LIST[250] = defines.Codes.NN_HANDSHAKE
defines.Codes.NOISE_NN_RQ_ENCRYPTED = defines.CodeItem(251, 'Noise NN Request Encrypted')
defines.Codes.LIST[251] = defines.Codes.NOISE_NN_RQ_ENCRYPTED
defines.Codes.NOISE_NN_RS_ENCRYPTED = defines.CodeItem(252, 'Noise NN Response Encrypted')
defines.Codes.LIST[252] = defines.Codes.NOISE_NN_RS_ENCRYPTED

defines.OptionRegistry.COMPRESSION = defines.OptionItem(number = 259, name = 'Compression', value_type = 0, repeatable = False, default = 0)
defines.OptionRegistry.LIST[259] = defines.OptionRegistry.COMPRESSION
# defines.OptionRegistry.ENCRYPTION = defines.OptionItem(number = 260, name = 'Encryption', value_type = 0, repeatable = False, default = 0)
# defines.OptionRegistry.LIST[260] = defines.OptionRegistry.ENCRYPTION

from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.option import Option
from coapthon.serializer import Serializer as OrigSerializer
import logging
import struct
import ctypes
import logging
import enum
import gzip
import bz2
import lzma
import zstd
from coapthon.utils import byte_len
from noise.connection import NoiseConnection

from coapthon.messages.request import Request
from coapthon.messages.response import Response

logger = logging.getLogger(__name__)


OPTION_COMPRESSION = 259
#OPTION_ENCRYPTION = 260

class Compression(enum.Enum):
	gzip = 1
	bz2 = 2
	# LZMA = "lzma"
	zstd = 3

	@classmethod
	def compress(cls, data, mode = None):
		if isinstance(mode, enum.Enum) and mode in cls.__members__.values():
			exec(f"import {mode.name}")
			coder = eval(mode.name)
			return coder.compress(data, 22 if mode == cls.zstd else 9)
		else:
			return data

	@classmethod
	def decompress(cls, compressed, mode = None):
		if isinstance(mode, enum.Enum) and mode in cls.__members__.values():
			exec(f"import {mode.name}")
			coder = eval(mode.name)
			return coder.decompress(compressed)
		else:
			return compressed


class Serializer(OrigSerializer):
	# @staticmethod
	# def deserialize(datagram, source = (None, None)):
	# 	mess = OrigSerializer.deserialize(datagram = datagram, source = source)
	# 	mess._code = int.from_bytes(datagram[1], 'big') if isinstance(datagram[1], bytes) else datagram[1]
	# 	return mess
	@staticmethod
	def deserialize(datagram, source = (None, None)):
		"""
		De-serialize a stream of byte to a message.

		:param datagram: the incoming udp message
		:param source: the source address and port (ip, port)
		:return: the message
		:rtype: Message
		"""
		try:
			fmt = "!BBH"
			pos = struct.calcsize(fmt)
			s = struct.Struct(fmt)
			values = s.unpack_from(datagram)
			first = values[0]
			code = values[1]
			mid = values[2]
			version = (first & 0xC0) >> 6
			message_type = (first & 0x30) >> 4
			token_length = (first & 0x0F)
			if Serializer.is_response(code):
				message = Response()
				message.code = code
			elif Serializer.is_request(code):
				message = Request()
				message.code = code
			else:
				message = Message()
			message.source = source
			message.destination = None
			message.version = version
			message.type = message_type
			message.mid = mid
			if token_length > 0:
				message.token = datagram[pos:pos+token_length]
			else:
				message.token = None

			pos += token_length
			current_option = 0
			values = datagram[pos:]
			length_packet = len(values)
			pos = 0
			while pos < length_packet:
				next_byte = struct.unpack("B", values[pos].to_bytes(1, "big"))[0]
				pos += 1
				if next_byte != int(defines.PAYLOAD_MARKER):
					# the first 4 bits of the byte represent the option delta
					# delta = self._reader.read(4).uint
					num, option_length, pos = Serializer.read_option_value_len_from_byte(next_byte, pos, values)
					logger.debug("option value (delta): %d len: %d", num, option_length)
					current_option += num
					# read option
					try:
						option_item = defines.OptionRegistry.LIST[current_option]
					except KeyError:
						(opt_critical, _, _) = defines.OptionRegistry.get_option_flags(current_option)
						if opt_critical:
							raise AttributeError("Critical option %s unknown" % current_option)
						else:
							# If the non-critical option is unknown
							# (vendor-specific, proprietary) - just skip it
							logger.warning("unrecognized option %d", current_option)
					else:
						if option_length == 0:
							value = None
						elif option_item.value_type == defines.INTEGER:
							tmp = values[pos: pos + option_length]
							value = 0
							for b in tmp:
								value = (value << 8) | struct.unpack("B", b.to_bytes(1, "big"))[0]
						elif option_item.value_type == defines.OPAQUE:
							tmp = values[pos: pos + option_length]
							value = tmp
						else:
							value = values[pos: pos + option_length]

						option = Option()
						option.number = current_option
						option.value = Serializer.convert_to_raw(current_option, value, option_length)

						message.add_option(option)
						if option.number == defines.OptionRegistry.CONTENT_TYPE.number:
							message.payload_type = option.value
					finally:
						pos += option_length
				else:

					if length_packet <= pos:
						# log.err("Payload Marker with no payload")
						raise AttributeError("Packet length %s, pos %s" % (length_packet, pos))
					message.payload = ""
					payload = values[pos:]
					if hasattr(message, 'payload_type') and message.payload_type in [
						defines.Content_types["application/octet-stream"],
						defines.Content_types["application/exi"],
						defines.Content_types["application/cbor"]
					]:
						message.payload = payload
					else:
						try:
							message.payload = payload.decode("utf-8")
						except AttributeError:
							message.payload = payload
					pos += len(payload)
			message._code = int.from_bytes(datagram[1], 'big') if isinstance(datagram[1], bytes) else datagram[1]
			return message
		except AttributeError:
			return defines.Codes.BAD_REQUEST.number
		except struct.error:
			return defines.Codes.BAD_REQUEST.number
		except UnicodeDecodeError as e:
			logger.debug(e)
			return defines.Codes.BAD_REQUEST.number

		### костыль
		# кастомный код CoAP для шифрования
		# в противном случае пришлось бы перелопатить дофига классов
		###
	@staticmethod
	def is_request(code):
		return defines.REQUEST_CODE_LOWER_BOUND <= code <= defines.REQUEST_CODE_UPPER_BOUND or code in \
			   (defines.Codes.NOISE_NN_RQ_ENCRYPTED.number, defines.Codes.NN_HANDSHAKE.number)

	@staticmethod
	def is_response(code):
		return defines.RESPONSE_CODE_LOWER_BOUND <= code <= defines.RESPONSE_CODE_UPPER_BOUND or \
			   code == defines.Codes.NOISE_NN_RS_ENCRYPTED.number


def convert_code(code):
	if isinstance(code, str): # HTTP method to CoAP request code
		req_codes_inv = {v: k for k, v in defines.Codes.LIST.items() if k < 5}
		for key in req_codes_inv.keys():
			if key.name.lower() == code.lower():
				return key.number
		raise ValueError(f"CoAP codes table has no value matching {code}")
	elif isinstance(code, int) and code < 200: # CoAP code to HTTP code
		binary = f"{code:08b}"
		return int(binary[:3], 2) * 100 + int(binary[3:], 2)
	else: # HTTP status code to CoAP code
		if code == 200:
			code = 205 # This Response Code is like HTTP 200 "OK" but only used in response to GET requests.
		coap_code = int(f"{code // 100:03b}{code % 100:05b}", 2)
		if coap_code in defines.Codes.LIST:
			return coap_code
		raise ValueError(f"CoAP codes table has no value matching {code}")


def build_message(type, code, payload = b'', content_type = None, options = None, uri_path = None, compression = None,
				  version = None, token = None, serialize = False, coder = None):
	message = Request() if uri_path else Message()
	if isinstance(type, int): message.type = type
	else: message.type = defines.Types.get(type, 1)

	if isinstance(code, int): message.code = code
	elif isinstance(code, defines.CodeItem): message.code = code.number
	else: message.code = defines.Codes.LIST.get(code, 0)

	if uri_path: message.uri_path = uri_path

	if isinstance(payload, bytes): message.payload = payload
	elif isinstance(payload, str): message.payload = bytes(payload, 'utf-8')
	else: message.payload = bytes(payload)

	if compression and isinstance(compression, Compression):
		message.payload = Compression.compress(message.payload, compression)
		c = Option()
		c.number = OPTION_COMPRESSION
		c.value = compression.value
		message.add_option(c)

	if isinstance(coder, NoiseConnection):
		message.payload = coder.encrypt(message.payload)
			# c = Option()
			# c.number = OPTION_ENCRYPTION
			# c.value = 1
			# message.add_option(c)


	if content_type in defines.Content_types: message.content_type = defines.Content_types[content_type]
	elif isinstance(content_type, int) and content_type in defines.Content_types.values():
		message.content_type = content_type

	if serialize:
		return Serializer.serialize(message)
	return message

def parse_message(datagram, coder = None):
	message = Serializer.deserialize(datagram)
	opt_nums = [opt.number for opt in message.options]

	if isinstance(coder, NoiseConnection):
		message.payload = coder.decrypt(message.payload)

	if defines.OptionRegistry.COMPRESSION.number in opt_nums:
		option = [opt for opt in message.options if opt.number == defines.OptionRegistry.COMPRESSION.number][0]
		message.payload = Compression.decompress(message.payload, Compression(option.value))

	return message

