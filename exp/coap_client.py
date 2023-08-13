import coapthon.client.coap as coap
from coapthon.serializer import Serializer
from coapthon import defines
from coapthon.messages.option import Option
import requests
import aiocoap
import enum

r = requests.get("https://api.lain-is.online/v1/lmg/network/test")

class Code(int, enum.Enum):
	def __new__(cls, value, label):
		# Initialise an instance of the Finger enum class
		obj = int.__new__(cls, value)
		# Calling print(type(obj)) returns <enum 'Finger'>
		# If we don't set the _value_ in the Enum class, an error will be raised.
		obj._value_ = value
		# Here we add an attribute to the finger class on the fly.
		# One may want to use setattr to be more explicit; note the python docs don't do this
		obj.label = label
		return obj

	GET = (0, 'GET')
	POST = (1, 'POST')
	PUT = (2, 'PUT')
	DELETE = (3, 'DELETE')
	SUBSCRIBE = (4, 'SUBSCRIBE')
	# 4-bit unsigned integer. This field indicates the CoAP Method of the request

	@classmethod
	def from_str(cls, input_str):
		for method in cls:
			if method.label == input_str or method.label.lower() == input_str:
				return method
		raise ValueError(f"{cls.__name__} has no value matching {input_str}")


def convert_code(code):
	if isinstance(code, str):
		req_codes_inv = {v: k for k, v in defines.Codes.LIST.items() if k < 5}
		for key in req_codes_inv.keys():
			if key.name.lower() == code.lower():
				return key.number
		else:
			raise ValueError(f"CoAP codes table has no value matching {code}")
	elif isinstance(code, int) and code < 200:
		binary = f"{code:08b}"
		return int(binary[:3], 2) * 100 + int(binary[3:], 2)
	else:
		return int(f"{code // 100:03b}{code % 100:05b}", 2)


message = coap.Message()
message.code = None
"""
	  8-bit unsigned integer, split into a 3-bit class (most
      significant bits) and a 5-bit detail (least significant bits),
      documented as "c.dd" where "c" is a digit from 0 to 7 for the
      3-bit subfield and "dd" are two digits from 00 to 31 for the 5-bit
      subfield.  The class can indicate a request (0), a success
      response (2), a client error response (4), or a server error
      response (5).  (All other class values are reserved.)  As a
      special case, Code 0.00 indicates an Empty data.  In case of a
      request, the Code field indicates the Request Method; in case of a
      response, a Response Code.
      
0.01-0.31 Indicates a request.  Values in this range are assigned by the "CoAP Method Codes" sub-registry (see Section 12.1.1).
2.00-5.31 Indicates a response.  Values in this range are assigned by the "CoAP Response Codes" sub-registry (see Section 12.1.2).
"""
message.payload = r.content
message.mid = 1
#data.content_type =
message.type = 0 # Confirmable (0), Non-confirmable (1), Acknowledgement (2), or Reset (3)

x = Serializer()
raw = x.serialize(message).raw