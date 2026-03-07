import threading
from http import HTTP_Server
from websocket import ping_scheduler


def main():
	server_thread = threading.Thread(target=HTTP_Server().start)
	ping_thread = threading.Thread(target=ping_scheduler, daemon=True)
	server_thread.start()
	ping_thread.start()


main()
