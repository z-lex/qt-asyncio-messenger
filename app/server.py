"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports
from collections import deque
from datetime import datetime

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
				login = decoded.replace("login:", "").replace("\n","")
				
				# проверяем, есть ли уже подключенный клиент
				# с таким логином
				if login in \
					[client.login for client in self.server.clients]:
					self.transport.write(
						f"Логин {login} занят, попробуйте другой".encode()
					)
					# дожидаемся отправки всех буферизованных данных
					# и закрываем соединение. после этого будет вызван
					# метод connection_lost
					self.transport.close()
				else:
					self.login = login	
					self.transport.write(
						f"Привет, {self.login}".encode()
					)
					self.send_history()
					
		else:
			self.send_message(decoded)

	def send_message(self, message):
		format_string = "[{0:%H:%M:%S}] <{1}>: {2}".\
			format(datetime.now(), self.login, message)
		encoded = format_string.encode()

		# добавляем сообщение к истории сервера 
		# уже в кодированном виде
		self.server.add_to_history(encoded_message=encoded)

		for client in self.server.clients:
			if client.login == self.login: continue
			client.transport.write(encoded)
	
	# функция отправки последних сообщений чата
	def send_history(self):
		if not self.server.is_history_empty():
			self.transport.write(
				f"\nПоследние сообщения чата:\n".encode()
			)
			for msg in self.server.history():
				self.transport.write(msg)
				self.transport.write('\n'.encode())
				


	def connection_made(self, transport: transports.Transport):
		self.transport = transport
		self.server.clients += [self]
		print("Соединение установлено")

	def connection_lost(self, exc):
		self.server.clients.remove(self)
		print("Соединение разорвано", exc if not exc is None else "")

class Server:
	clients: list
	__history: 'deque'
	
	def __init__(self):
		self.clients = []

		# очередь для хранения максимум 10 
		# последних сообщений
		self.__history = deque(maxlen=10)

	def create_protocol(self):
		return ClientProtocol(self)

	# метод добавления сообщения к истории сообщений сервера
	def add_to_history(self, encoded_message):
		self.__history.append(encoded_message)

	# функция-генератор для получения истории сообщений
	def history(self):
		yield from list(self.__history)

	# функция проверки наличия сообщений в истории сообщений
	def is_history_empty(self):
		return len(self.__history) == 0
		
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
