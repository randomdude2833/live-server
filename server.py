import socket
import webbrowser
import threading
import json

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
		socket.addEventListener("open", (e) => {{
			socket.send("Hello Server");
		}});
	</script>
	"""
	return html.replace("</body>", reload_script + "</body>")

		
if __name__ == "__main__":
	main()
