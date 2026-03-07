def extract_request_headers(request_buffer):
	header, _, body= request_buffer.partition(b"\r\n\r\n")
	header = header.decode()
	header_fields = header.split("\r\n")
	request_headers = {}
	request_headers["request-line"] = header_fields[0]
	for header_field in header_fields[1:]:
		key, value = header_field.split(":", 1)
		request_headers[key.lower()] = value.strip()
	return request_headers


def inject_reload_script(html):
    reload_script = """
    <script>
        const socket = new WebSocket("ws://127.0.0.1:28333");
		socket.addEventListener("open", (e) => {
			console.log("Connection opened successfully")
		});
        socket.addEventListener("message", (e) => {
            console.log("Message from server: ", e.data);
        });
    </script>
    """
    return html.replace("</body>", reload_script + "</body>")
