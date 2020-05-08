"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports

class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None
    def send_history(self):
        if self.server.history:                                                                        #Если есть история сообщений(список не пуст)
            self.transport.write(                                                                      #Печатаем последние 10 сообщений
                ("Последние 10 сообщений: \r\n"+"\r\n".join(self.server.history[-10::])).encode()
            )
        else:                                                                                          # Иначе, если истории сообщений нет, выводим соооответствующий текст
            self.transport.write(
                "Предыдущих сообщений нет.".encode()
            )
    def data_received(self, data: bytes):
        decoded = data.decode()
        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                wanted_login = decoded.replace("login:","").replace("\r\n","")                          # Создаем временную переменую логина
                if self.server.login_exists(wanted_login):                                              # Если введеный логин есть в списке
                    self.transport.write(                                                               # Отправляем соответствующее сообщение
                        f"Логин {wanted_login} занят, попробуйте другой.".encode()
                    )
                    self.transport.write(                                                               # Предепруждаем, что соединение будет разорвано
                        f"Соединение будет разорвано.".encode()
                    )
                    self.transport.close()                                                              # Отключаем от сервера соединение клиента
                else:
                    self.login = wanted_login                                                           # Иначе добавляем логин в список
                    self.transport.write(                                                               # Отправляем "приветку"
                        f"Привет, {self.login} !".encode()
                    )
                    self.send_history()                                                                 # И вызываем функцию отправки последних 10 сообщений

        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        self.server.history.append(format_string)
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login and client.login != None:                # Если клиент не "мы" и зарегистрирован в системе
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport =  transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list                                                                   # Добавляеем список с историей сообщений

    def __init__(self):
        self.clients = []
        self.history = []
    def login_exists(self, wanted_login):                                           # Функция определения существующего логина
        for client in self.clients:                                                 # Перебираем все объекты в списки clients
             if client.login == wanted_login:                                       # Если искомый логин существует
                return True                                                         # Возвращаем true
        else:
            return False                                                            # Иначе false

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")