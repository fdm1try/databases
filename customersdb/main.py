import psycopg2
import sys
import re

DB_NAME = 'postgres'
DB_USER = 'postgres'
DB_PASSWORD = ''
DB_HOST = '127.0.0.1'
DB_PORT = None
PAGE_SIZE = 5


class InvalidPhoneFormat(Exception):
    pass


def postgres_table_diff(cursor: psycopg2.extensions.cursor, params: dict):
    """
    :param cursor: psycopg2 cursor
    :param params: should be like {table_name: [(column, data_type), ...] }
    :return: True if one of the tables does not match the specified parameters
    """
    tables = params.keys()
    if tables == '':
        return None
    mask = ('%s,' * len(tables))[:-1]
    query = f'SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_name IN ({mask});'
    cursor.execute(query, tuple(tables))
    schema = cursor.fetchall()
    if not len(schema):
        return True
    checked = set()
    data = [
        (table_name, column[0], column[1])
        for table_name, columns in params.items()
        for column in columns
    ]
    for column in schema:
        i = data.index(column)
        if i >= 0:
            checked.add(i)
        else:
            return True
    return False if len(checked) == len(data) else True


class Phone:
    def __init__(self, phone_number: str, phone_id: int, client=None):
        self._id = phone_id
        self._client = client
        self._number = self.__class__.parse(phone_number)

    def __str__(self):
        return re.sub(r'^(\d{1,2})(\d{3})(\d{3})(\d{2})(\d{2})', r'+\1 (\2) \3 \4-\5', self._number)

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def parse(phone_number: str):
        """
        :param phone_number: phone number in international format
        :return: removes all characters from the string except numbers
        """
        if re.match(r'^\d{1,2}\d{10}$', phone_number):
            return phone_number
        phone = re.sub(r'\D', '', phone_number)
        if not re.match(r'^\d{1,2}\d{10}$', phone):
            raise InvalidPhoneFormat('Invalid phone number format')
        return phone

    @property
    def id(self):
        return self._id

    @property
    def number(self):
        return self._number

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, client):
        if not isinstance(client, Client):
            raise Exception('client param should be a Client instance')
        self._client = client


class Clients:
    def __init__(self, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT):
        """
        :param database: name of database
        :param user: user name
        :param password: password
        :param host: IP-address or domain name
        :param port: port
        """
        self.connection = psycopg2.connect(database=database, user=user, password=password, host=host, port=port)

    def __del__(self):
        self.connection.close()

    def check_schema(self):
        """
        :return: True if all tables exist in the database
        """
        with self.connection.cursor() as cur:
            return not postgres_table_diff(cur, {
                    'client': [('id', 'integer'), ('first_name', 'text'), ('last_name', 'text'), ('email', 'text')],
                    'client_phone': [('id', 'integer'), ('client_id', 'integer'), ('phone', 'text')]
                })

    def create_schema(self):
        """
        :return: Creates the necessary tables in the database, returns None
        """
        with self.connection.cursor() as cur:
            cur.execute('''
                DROP TABLE IF EXISTS client_phone;
                DROP TABLE IF EXISTS client;                    
                CREATE TABLE client (id SERIAL PRIMARY KEY, first_name TEXT, last_name TEXT, email TEXT);
                CREATE TABLE client_phone (
                    id SERIAL PRIMARY KEY,
                    client_id INTEGER REFERENCES client,
                    phone TEXT CHECK(phone ~ '^\d{1,2}\d{10}$')
                );
            ''')
            self.connection.commit();

    def add(self, first_name=None, last_name=None, email=None):
        """
        :param first_name: client first name
        :param last_name:client last name
        :param email: client e-mail address
        :return: Adds the client to the database, returns a Client instance
        """
        with self.connection.cursor() as cur:
            cur.execute('INSERT INTO client(first_name, last_name, email) VALUES (%s, %s, %s) RETURNING id;',
                        (first_name, last_name, email,))
            self.connection.commit()
            client_id = cur.fetchone()[0]
            return Client(self, client_id, first_name, last_name, email)

    def change(self, client_id: int, prop: str, *params):
        """
        :param client_id: client ID in the database
        :param prop: can be one of: first_name, last_name, email, phone.
        :param params: if the prop is 'phone', two parameters are required
        (the first is an id of existing number, the second is a new number).
        In another case, the first parameter is the new value
        :return: True if value changed
        """
        if prop == 'phone':
            if len(params) < 2:
                raise Exception('To change phone number you should specify old number and then new phone number!')
            phone_id, new_number = params
            new_number = Phone.parse(new_number) if not isinstance(new_number, Phone) else new_number.number
            with self.connection.cursor() as cur:
                cur.execute('UPDATE client_phone SET phone=%s WHERE id=%s RETURNING id;', (new_number, phone_id,))
                if cur.fetchone()[0] == phone_id:
                    self.connection.commit()
                    return True
                return False
        if prop not in ['first_name', 'last_name', 'email']:
            raise Exception(f'Unknown parameter {prop}')
        with self.connection.cursor() as cur:
            cur.execute(f'UPDATE client SET {prop}=%s WHERE id=%s RETURNING id;', (params[0], client_id,))
            if cur.fetchone()[0] == client_id:
                self.connection.commit()
                return True
            return False

    def add_phone(self, client_id: int, phone: str):
        """
        :param client_id: client ID in the database
        :param phone: phone number in international format
        :return: adds a phone number for the specified client, returns an instance of Phone
        """
        phone_number = Phone.parse(phone)
        with self.connection.cursor() as cur:
            cur.execute('INSERT INTO client_phone (client_id, phone) VALUES (%s, %s) RETURNING id;', (client_id, phone_number,))
            if phone_id := cur.fetchone()[0]:
                self.connection.commit()
                return Phone(phone_number, phone_id)

    def list_phone(self, client_id):
        """
        :param client_id: client ID in the database
        :return: list of client phone numbers
        """
        with self.connection.cursor() as cur:
            cur.execute('SELECT id, phone FROM client_phone WHERE client_id=%s;', (client_id,))
            return [Phone(item[1], item[0]) for item in cur.fetchall()]

    def list(self):
        """
        :return: list of clients
        """
        with self.connection.cursor() as cur:
            cur.execute('SELECT * FROM client;')
            return [Client(self, *client) for client in cur.fetchall()]

    def find(self, filters: dict):
        """
        :param filters: should be like {column_name: value, ...}, for example {'first_name': 'Client`s first name'}
        :return: list of clients
        """
        filter_parts = []
        filter_by_phone = False
        for key, value in filters.items():
            if key == 'phone':
                filter_by_phone = True
                filter_parts += [('client_phone.phone', Phone.parse(value),)]
            elif key in ['first_name', 'last_name', 'email']:
                filter_parts += [(f'client.{key}', f'%{value.lower()}%',)]
        with self.connection.cursor() as cur:
            query = 'SELECT client.* FROM client'
            if filter_by_phone:
                query += ' JOIN client_phone ON client_phone.client_id = client.id'
            query += f' WHERE {" AND ".join(["LOWER(" + v[0] + ") LIKE %s" for v in filter_parts])};'
            cur.execute(query, tuple([v[1] for v in filter_parts]))
            return [Client(self, *client) for client in cur.fetchall()]

    def remove(self, client_id):
        """
        :param client_id: client ID in the database
        :return: True if removed
        """
        self.remove_phone(client_id)
        with self.connection.cursor() as cur:
            cur.execute('DELETE FROM client WHERE id=%s RETURNING id;', (client_id,))
            if client_id == cur.fetchone()[0]:
                self.connection.commit()
                return True
            return False

    def remove_phone(self, client_id, phone: Phone = None):
        """
        :param client_id: client ID in the database
        :param phone: phone (if not passed, all the client's phone numbers will be deleted)
        :return: True if removed
        """
        query = 'DELETE FROM client_phone WHERE client_id = %s'
        if phone:
            query += ' AND id=%s'
        with self.connection.cursor() as cur:
            cur.execute(f'{query} RETURNING id;', (client_id, phone.id,) if phone else (client_id, ))
            self.connection.commit()
            return True


class Client:
    def __init__(self, parent: Clients, client_id: int, first_name: str, last_name: str, email: str):
        """
        :param parent: instance of Clients
        :param client_id: client ID in the database
        :param first_name: client`s first name
        :param last_name: client`s last name
        :param email: client`s e-mail address
        """
        self.clients = parent
        self._id = client_id
        self._first_name = first_name
        self._last_name = last_name
        self._email = email

    def __str__(self):
        return f'{self.first_name} {self.last_name} [{self.email}]'

    def __repr__(self):
        return self.__str__()

    @property
    def id(self):
        return self._id

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, name):
        if self.clients.change(self._id, 'first_name', name):
            self._first_name = name

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, name):
        if self.clients.change(self._id, 'last_name', name):
            self._last_name = name

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        if self.clients.change(self._id, 'email', email):
            self._email = email

    @property
    def phones(self):
        """
        :return: list of client`s phones numbers
        """
        if not self._id:
            raise Exception('Client not exist')
        phone_list = self.clients.list_phone(self._id)
        for phone in phone_list:
            phone.client = self
        return phone_list

    def add_phone(self, phone: str):
        """
        :param phone: phone number
        :return: Phone instance if added
        """
        if not self._id:
            raise Exception('Client not exist')
        if phone := self.clients.add_phone(self._id, phone):
            return phone

    def change_phone(self, old: Phone, new: str):
        """
        :param old: the phone number must be an instance of the Phone
        :param new: phone number
        :return: True if changed
        """
        if not self._id:
            raise Exception('Client not exist')
        new = Phone.parse(new)
        if self.clients.change(self._id, 'phone', old.id, new):
            return True

    def remove_phone(self, phone: Phone):
        """
        :param phone: phone number to delete
        :return: True if removed
        """
        if not self._id:
            raise Exception('Client not exist')
        return self.clients.remove_phone(self._id, phone)

    def remove(self):
        """
        :return: True if removed
        """
        if self.clients.remove(self._id):
            self._id = None
            self._first_name = None
            self._last_name = None
            self._email = None
            return True


class App:
    @staticmethod
    def get_credentials():
        """
        :return: requests data from the user to connect to the database and returns them as a tuple
        """
        print(
            'Необходимо указать данные для подключения к базе данных. '
            'Оставьте поле пустым чтобы выйти.'
        )
        database = input('имя базы данных: ')
        if not len(database):
            sys.exit()
        user = input('имя пользователя: ')
        if not len(user):
            sys.exit()
        password = input('пароль: ')
        if not len(password):
            sys.exit()
        return database, user, password

    def __init__(self, **kwargs):
        """
        :param kwargs: database connection parameters (psycopg2.connect)
        """
        while True:
            try:
                self.clients = Clients(**kwargs)
                break
            except Exception as e:
                print(f'Не удалось подключиться к базе данных!\nОшибка: {e}')
                database, user, password = self.__class__.get_credentials()
                kwargs = {
                    **kwargs,
                    'database': database,
                    'user': user,
                    'password': password
                }
        if not self.clients.check_schema():
            print('В базе данных нет необходимых для работы таблиц или их структура не подходит.')
            if input('Создать таблицы? (да/нет): ').lower().startswith('д'):
                self.clients.create_schema()
            else:
                print('Невозможно продолжить, программа завершена.')
                sys.exit()

    def add_client(self):
        """
        :return: adds a new client and returns to the main menu
        """
        first_name = input('Введите имя: ')
        last_name = input('Введите фамилию: ')
        email = input('Введите e-mail адрес: ')
        if re.match(r'^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$', email):
            if client := self.clients.add(first_name, last_name, email):
                return self.client_menu(client)
        else:
            print('Не удалось добавить пользователя, e-mail адрес указан не верно.')
            return self.add_client()
        return self.main_menu()

    def find_client(self):
        """
        :return: client search menu, returns to the client select menu
        """
        print()
        filters = {}
        while True:
            print('Критерии поиска:')
            print('1. имя' + (f' [{filters.get("first_name")}]' if 'first_name' in filters else ''))
            print('2. фамилия' + (f' [{filters.get("last_name")}]' if 'last_name' in filters else ''))
            print('3. адрес e-mail' + (f' [{filters.get("email")}]' if 'email' in filters else ''))
            print('4. номер телефона' + (f' [{filters.get("phone")}]' if 'phone' in filters else ''))
            print('9. начать поиск\n0. выйти в главное меню')
            user_choice = int(input('введите номер: '))
            if user_choice in [1, 2, 3, 4]:
                value = input('введите искомое значение: ')
                key = [None, 'first_name', 'last_name', 'email', 'phone'][user_choice]
                if key == 'phone':
                    value = Phone.parse(value)
                if key in filters:
                    if input(f'Этот критерий поиска уже указан, заменить на "{value}"? (да/нет): ').lower().startswith('д'):
                        filters[key] = value
                else:
                    filters[key] = value
            if user_choice == 0:
                return self.main_menu()
            if user_choice == 9:
                client_list = self.clients.list() if not len(filters) else self.clients.find(filters)
                return self.client_list_menu(client_list)

    def client_list_menu(self, client_list: dict):
        """
        :param client_list: list of clients available for selection
        :return: returns to the menu of the selected client
        """
        print()
        client_count = len(client_list)
        if not client_count:
            print('Клиентов не найдено')
            return self.main_menu()
        client_ids = list(range(1, client_count + 1))
        page_count = client_count // PAGE_SIZE + (1 if client_count % PAGE_SIZE else 0)
        page = 1
        while True:
            i = (page - 1) * PAGE_SIZE
            print(f'Страница {page}/{page_count}:')
            print(*[
                f'{client_id}. {client.first_name} {client.last_name} [{client.email}]'
                for client_id, client in zip(client_ids[i:i + PAGE_SIZE], client_list[i:i + PAGE_SIZE])
            ], sep='\n')
            if page > 1:
                print('<. Предыдущая страница')
            if page < page_count:
                print('>. Следующая страница')
            print('0. Главное меню')
            user_choice = input('введите номер клиента для выбора: ')
            if user_choice == '<':
                if page > 1:
                    page -= 1
                continue
            elif user_choice == '>':
                if page < page_count:
                    page += 1
                continue
            elif int(user_choice) in client_ids:
                client = client_list[int(user_choice) - 1]
                return self.client_menu(client)
            return self.main_menu()

    def client_menu(self, client: Client):
        """
        :param client: client
        :return: the client menu works recursively, can return to the main menu or the phone number editing menu
        """
        print()
        print(f'Клиент: {client.first_name} {client.last_name} [{client.email}]')
        print('1. телефонные номера\n2. изменить имя\n3. изменить фамилию\n4. изменить email\n5. удалить клиента'
              '\n0. главное меню')
        user_choice = int(input('введите номер: '))
        if user_choice == 1:
            return self.phone_menu(client)
        elif user_choice in [2, 3, 4]:
            value = input('Введите новое значение: ')
            if user_choice == 2:
                client.first_name = value
            elif user_choice == 3:
                client.last_name = value
            elif user_choice == 4:
                client.email = value
        elif user_choice == 5:
            if client.remove():
                print('Клиент успешно удалён')
                return self.main_menu()
        elif user_choice == 0:
            return self.main_menu()
        return self.client_menu(client)

    def phone_select_menu(self, phone_list: list):
        """
        :param phone_list: list of phone numbers available for selection
        :return: the phone number selected by the user
        """
        print()
        phone_count = len(phone_list)
        if not phone_count:
            print('Номера телефонов не найдены')
            return
        page_count = phone_count // PAGE_SIZE + (1 if phone_count % PAGE_SIZE else 0)
        phone_ids = list(range(1, phone_count + 1))
        page = 1
        while True:
            print(f'Выберите номер телефона из списка | страница {page}/{page_count}:')
            i = (page-1) * PAGE_SIZE
            print(*[
                f'{list_id}. {phone}'
                for list_id, phone in zip(phone_ids[i:i + PAGE_SIZE], phone_list[i:i + PAGE_SIZE])
            ], sep='\n')
            if page > 1:
                print('<. Предыдущая страница')
            if page < page_count:
                print('>. Следующая страница')
            print('0. Назад к списку клиентов')
            user_choice = input('введите порядковый номер: ')
            if user_choice == '<':
                if page > 1:
                    page -= 1
                continue
            elif user_choice == '>':
                if page < page_count:
                    page += 1
                continue
            elif int(user_choice) in phone_ids:
                return phone_list[int(user_choice) - 1]

    def phone_menu(self, client: Client, phone: Phone = None):
        """
        :param client: client
        :param phone: client`s phone number
        :return: the menu for changing phone numbers works recursively, but can return to the main menu
        """
        print()
        title = "Телефонные номера" if not phone else str(phone)
        print(f'{title} | {client}')
        print('1. показать все\n2. добавить номер телефона\n3. изменить номер телефона\n4. удалить номер телефона\n'
              '0. главное меню')
        user_choice = int(input('введите номер меню: '))
        if user_choice == 1:
            selected_phone = self.phone_select_menu(client.phones)
            return self.phone_menu(client, selected_phone)
        elif user_choice == 2:
            while True:
                user_input = input('Введите номер телефона: ')
                try:
                    phone = client.add_phone(user_input)
                    print(f'номер телефона {phone} добавлен')
                    return self.phone_menu(client)
                except InvalidPhoneFormat:
                    print('Номер телефона введён не корректно, введите номер телефона в международном формате.')
        elif user_choice in [3, 4]:
            phone = phone or self.phone_select_menu(client.phones)
            if user_choice == 3:
                while True:
                    user_input = input('Введите новый номер телефона: ')
                    try:
                        new_phone = Phone.parse(user_input)
                        break
                    except InvalidPhoneFormat:
                        print('Номер телефона введён не корректно, введите номер телефона в международном формате.')
                if client.change_phone(phone, new_phone):
                    print('Номер успешно изменён')
                    return self.phone_menu(client)
            else:
                if client.remove_phone(phone):
                    print('Номер успешно удалён')
                    return self.phone_menu(client)
        elif user_choice == 0:
            return self.main_menu()
        return self.phone_menu(client, phone)

    def main_menu(self):
        """
        :return: through the main menu, you can get to the client search menu and the client add menu.
        """
        print(
            '\nГлавное меню:\n1. Добавить клиента\n2. Найти клиента'
            '\n0. Выйти из программы'
        )
        user_choice = int(input('Что вы хотите сделать? Введите номер: '))
        if user_choice not in [1, 2]:
            return None
        return [None, self.add_client, self.find_client][user_choice]()


if __name__ == '__main__':
    app = App()
    app.main_menu()
