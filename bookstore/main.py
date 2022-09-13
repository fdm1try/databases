import sqlalchemy
from sqlalchemy.orm import sessionmaker
import model
from model import Publisher
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
    try:
        print(session.query(Publisher).filter(Publisher.id == int(user_input)).one())
    except Exception as e:
        print(session.query(Publisher).filter(Publisher.name == user_input).one())

    session.close()
