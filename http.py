import os
import socket
import threading
import json
from helpers import extract_request_headers, inject_reload_script
from websocket import upgrade_connection, is_ws_handshake_request, listen_for_websocket_frames


class HTTP_Server:
	def create(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind(("", 28333))
		self.socket.listen(5) # test later 

	def start(self):
		self.create()
		print("Server started: http://localhost:28333")
		while True:
			client, addr = self.socket.accept()
			client_thread = threading.Thread(target=self.handle_client, args=(client, addr), daemon=True)
			client_thread.start()

	def handle_client(self, client, addr):
		print(f"New connection: {addr}")
		
		request_buffer, connection_closed = self.receive_client_request(client)
		if connection_closed:
			client.close()
			return

		request_headers = extract_request_headers(request_buffer)	
		print(json.dumps(request_headers, indent=4))	

		if is_ws_handshake_request(request_headers):
			upgrade_connection(client, request_headers)
			listen_for_websocket_frames(client)
			return 

		self.serve(client, "index.html")
		client.close()

	def receive_client_request(self, client):
		connection_closed = False
		buffer = bytearray()
		while True:
			bytes_received = client.recv(2048)

			if not bytes_received:
				connection_closed = True
				break
				
			buffer.extend(bytes_received)
			if b"\r\n\r\n" in buffer:
				break

		return buffer, connection_closed
	

	def serve(self, client, file):
		with open(f"files/{file}") as html_file:
			html = html_file.read()

		html = inject_reload_script(html)
		html_bytes = html.encode()
		response = (
			"HTTP/1.1 200 OK\r\n"
			"Content-Type: text/html\r\n"
			f"Content-Length: {len(html_bytes)}\r\n"
			"Connection: close\r\n"
			"\r\n"
		).encode()
		response += html_bytes
		client.sendall(response)
		
		
		
		
		
