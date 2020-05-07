"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports

class ClientProtocol(asyncio.Protocol):
	login: str
	server: 'Server'

	# connection link
	transport: transports.Transport
	
	def __init__(self, server: 'Server'):
		self.server = server
		self.login = None

	def data_received(self, data: bytes):
		decoded = data.decode()
		print(decoded)

		if self.login is None:
			if decoded.startswith("login:"):
				self.login = decoded.replace("login:", "").replace("\n","")
				self.transport.write(
					f"Привет, {self.login}".encode()
				)
		else:
			self.send_message(decoded)

	def send_message(self, message):
		format_string = f"<{self.login}>: {message}"
		encoded = format_string.encode()
		#import pdb; pdb.set_trace()	
		for client in self.server.clients:
			if client.login == self.login: continue
			client.transport.write(encoded)
		

				

	def connection_made(self, transport: transports.Transport):
		self.transport = transport
		self.server.clients += [self]
		print("Соединение установлено")

	def connection_lost(self, exc):
		self.server.clients.remove(self)
		print("Соединение разорвано", exc)

class Server:
	clients: list
	
	def __init__(self):
		self.clients = []

	def create_protocol(self):
		return ClientProtocol(self)

	async def start(self):
		print("Запускается сервер")
		loop = asyncio.get_running_loop()
		# for incoming connections
		coroutine = await loop.create_server(
			self.create_protocol,
			"127.0.0.1",
			8888
		)

		print("Сервер запущен")

		await coroutine.serve_forever()
	
process = Server()
try:
	asyncio.run(process.start())

# to avoid getting many error messages on Ctrl+C
except KeyboardInterrupt:
	print("Сервер остановлен вручную")
