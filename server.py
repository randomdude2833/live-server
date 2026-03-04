import socket
import webbrowser
import threading
import json
import hashlib
import base64

HOST = "127.0.0.1"
PORT = 28333

def main():
	server_thread = threading.Thread(target=start_server)
	server_thread.start()
	webbrowser.open(f"http://{HOST}:{PORT}")
		

def start_server():
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	
	server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server.bind(("", PORT))
	server.listen(1)
	
	while True:
		client, addr = server.accept()
		process_request(client, addr)	


def process_request(client, addr):
	print("---------------------------------------------")
	print(f"New connection: {addr}")

	buffer = b""
	while True:
		data_bytes = client.recv(2048)
		if not data_bytes:
			client.close()
			return

		buffer += data_bytes
		if b"\r\n\r\n" in buffer:
			break
	
	header = buffer.split(b"\r\n\r\n")[0].decode()
	header_lines = header.split("\r\n")
	request_line = header_lines[0]
	headers = {}
	headers["request-line"] = request_line

	for header_line in header_lines[1:]:
		key, value = header_line.split(":", 1)
		headers[key.lower()] = value.strip()
	print(json.dumps(headers, indent=4))	

	if "upgrade" in headers and headers["upgrade"].lower() == "websocket" and "sec-websocket-key" in headers:
		send_websocket_handshake_response(client, headers["sec-websocket-key"])
		send_frame(client)
		return
		
	with open("index.html") as file:
		html = file.read()
	
	html = inject_reload_script(html)
	html_bytes = html.encode()

	response = (
		"HTTP/1.1 200 OK\r\n"
		"Content-Type: text/html\r\n"
		f"Content-Length: {len(html_bytes)}\r\n"
		"Connection: close\r\n"
		"\r\n"
	).encode() + html_bytes

	client.sendall(response)
	client.close()


def inject_reload_script(html):
	reload_script = f"""
	<script>
		const socket = new WebSocket("ws://{HOST}:{PORT}");
		socket.addEventListener("message", (e) => {{
			console.log("Message from server: ", e.data);
		}});
	</script>
	"""
	return html.replace("</body>", reload_script + "</body>")


def send_websocket_handshake_response(client, sec_websocket_key):
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

def send_frame(client):
	message = "Hello client"
	payload = message.encode()
	length = len(payload)
	
	frame = bytearray()
	# FIN (1 bit) RSV1-3 (3 bits) opcode (4 bits)
	first_byte = 0x81 # 10000001
	frame.append(first_byte)
	frame.append(length)
	frame.extend(payload)
	client.sendall(frame)


		
if __name__ == "__main__":
	main()





















