import sqlalchemy
from sqlalchemy.orm import sessionmaker
import model
from model import Publisher, Book, Stock, Shop
import json
import os

DB_TYPE = os.getenv('DB_TYPE') or 'postgresql'
DB_NAME = os.getenv('DB_NAME') or 'postgres'
DB_USER = os.getenv('DB_USER') or 'postgres'
DB_PASSWORD = os.getenv('DB_PASSWORD') or 'postgres'
DB_HOST = os.getenv('DB_HOST') or 'localhost'
DB_PORT = os.getenv('DB_PORT') or 5432

TEST_DATA_FILE_PATH = './fixtures/tests_data.json'


def fill_in_tables(session: sqlalchemy.orm.session.Session):
    with open(TEST_DATA_FILE_PATH) as file:
        data = json.load(file)
    session.add_all([
        getattr(model, item['model'].title())(**item['fields'])
        for item in data
    ])
    session.commit()


if __name__ == '__main__':
    DSN = f'{DB_TYPE.lower()}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = sqlalchemy.create_engine(DSN)
    model.create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()
    fill_in_tables(session)
    user_input = input('Введите ID или наименование издателя: ')
    publisher_shops = (
        session.query(Publisher.name, Shop.name)
        .join(Stock, Stock.id_shop == Shop.id)
        .join(Book, Book.id == Stock.id_book)
        .join(Publisher, Book.id_publisher == Publisher.id)
        .filter(Publisher.id == int(user_input) if user_input.isdigit() else Publisher.name == user_input)
        .distinct(Shop.name)
        .group_by(Publisher.name, Shop.name)
    ).all()
    if not len(publisher_shops):
        print('Издатель не найден')
    else:
        publisher = publisher_shops[0][0]
        shops = [item[1] for item in publisher_shops]
        print(f'Издатель: {publisher}')
        print(f'Его книги продаются в магазинах: {", ".join(shops)}')
