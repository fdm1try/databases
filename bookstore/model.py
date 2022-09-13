import sqlalchemy
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Publisher(Base):
    __tablename__ = 'publisher'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text, unique=True)

    def __str__(self):
        return f'{self.id}: {self.name}'


class Shop(Base):
    __tablename__ = 'shop'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text, unique=True)


class Book(Base):
    __tablename__ = 'book'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    id_publisher = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("publisher.id"), nullable=False)

    publisher = relationship(Publisher, backref='publisher')


class Stock(Base):
    __tablename__ = 'stock'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    id_book = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("book.id"), nullable=False)
    id_shop = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("shop.id"), nullable=False)
    count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    book = relationship(Book, backref='book')
    shop = relationship(Shop, backref='shop')


class Sale(Base):
    __tablename__ = 'sale'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    date_sale = sqlalchemy.Column(sqlalchemy.Date)
    id_stock = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("stock.id"), nullable=False)
    count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    stock = relationship(Stock, backref='stock')


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


