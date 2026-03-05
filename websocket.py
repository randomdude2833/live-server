import hashlib
import base64


def is_ws_handshake_request(request_headers):
	request_line = request_headers["request-line"]
	method, path, version = request_line.split()
	if method != "GET":
		return False

	sec_websocket_key = request_headers.get("sec-websocket-key")
	if sec_websocket_key is None:
		return False

	upgrade_websocket = request_headers.get("upgrade")
	if upgrade_websocket is None:
		return False

	return upgrade_websocket.lower() == "websocket"


def upgrade_connection(client, request_headers):
	sec_websocket_key = request_headers["sec-websocket-key"]
	magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
	added = sec_websocket_key + magic_string
	hashed = hashlib.sha1(added.encode()).digest()
	encoded = base64.b64encode(hashed)

	response = (
		"HTTP/1.1 101 Switching Protocols\r\n"
		"Upgrade: websocket\r\n"
		"Connection: Upgrade\r\n"
		f"Sec-WebSocket-Accept: {encoded.decode()}\r\n"
		"\r\n"
	).encode()

	client.sendall(response)


def listen_for_websocket_frames(client):
	while True:
		# read first two bytes of the frame
		frame = client.recv(2)
		first_byte = int.from_bytes(frame[:1])
		second_byte = int.from_bytes(frame[1:])

		fin = first_byte >> 7
		opcode = first_byte & 0x0F
		payload_length = second_byte & 0x7F
		mask = client.recv(4)
		payload = client.recv(payload_length)
		
		unmasked_payload = bytearray()
		offset = 0
		for byte in payload:
			unmasked_payload.append(byte ^ mask[offset % 4])
			offset += 1
			
		print("Message from client:", unmasked_payload.decode())

			
		
			
		
		

