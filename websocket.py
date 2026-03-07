import hashlib
import base64
import threading
import time


clients = []
pings_sent = []
pongs_received = []


def is_ws_handshake_request(request_headers):
	request_line = request_headers["request-line"]
	method, path, version = request_line.split()
	if method.lower() != "get":
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
	clients.append(client)	

	while True:
		try:
			frame = recv_exact(client, 2)
		except:
			close_connection(client)
			return
			
		first_byte = frame[0]
		second_byte = frame[1]

		fin = first_byte >> 7
		opcode = first_byte & 0x0F
		print("opcode:", opcode)
		mask = second_byte >> 7
		payload_length = second_byte & 0x7F
		
		# valid control frames will have:
		# 1. FIN  = 1
		# 2. mask = 1
		# 3. payload length <= 125
		# 4. one of these opcodes:
		# 	4.1 0x8 (close)
		# 	4.2 0x9 (ping)
		# 	4.1 0xA (pong)
		if fin == 0 or mask == 0 or payload_length > 125:
			close_connection(client)
			return
			
		if opcode != 0x9 and opcode != 0xA and opcode != 0x8:
			close_connection(client)
			return 
			
		try:
			masked_payload_with_masking_key = recv_exact(client, 4 + payload_length)
		except:
			close_connection(client)
			return

		if opcode == 0x9: # ping
			print("received ping from:", client)
			send_pong(client, masked_payload_with_masking_key)
		elif opcode == 0xA: # pong
			print("received pong from:", client)
			pongs_received.append(client)
		else: # close
			close_connection(client)
			return 


def close_connection(client):
	pass
	

def send_ping(client):
	ping = bytearray([0x89, 0x0])
	client.sendall(ping)
	pings_sent.append(client)

				
def send_pong(client, masked_payload_with_masking_key):
	masking_key = masked_payload_with_masking_key[:4]
	masked_payload = masked_payload_with_masking_key[4:] 

	offset = 0
	payload = bytearray()
	for byte in masked_payload:
		payload.append(byte ^ masking_key[offset % 4])
		offset += 1
	
	pong = bytearray([0x8A, len(payload)])
	pong.extend(payload)
	client.sendall(pong)	
	

def recv_exact(client, bytes_to_recv):
	buffer = bytearray()
	
	while len(buffer) < bytes_to_recv:
		bytes_received = client.recv(bytes_to_recv - len(buffer))
		if len(bytes_received) == 0:
			raise ConnectionError("Client closed connection.")
		buffer.extend(bytes_received)
	
	return buffer


def ping_scheduler():
	while True:
		print("PING SCHEDULER")
		# check if received and sent match
		pings_sent.clear()
		for client in clients:
			send_ping(client)

		time.sleep(5)
