import sqlalchemy
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Publisher(Base):
    __tablename__ = 'publisher'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    books = relationship("Book", backref='publisher')

    def __str__(self):
        return self.name


class Shop(Base):
    __tablename__ = 'shop'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text, unique=True)

    stock = relationship('Stock', back_populates='shop')

    def __str__(self):
        return f'{self.name}'


class Book(Base):
    __tablename__ = 'book'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    id_publisher = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("publisher.id"), nullable=False)

    stock = relationship('Stock', back_populates='book')

    def __str__(self):
        return f'{self.title} ({self.publisher})'


class Stock(Base):
    __tablename__ = 'stock'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    id_book = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("book.id"), nullable=False)
    id_shop = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("shop.id"), nullable=False)
    count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    sales = relationship('Sale', backref='stock')
    book = relationship('Book', back_populates='stock')
    shop = relationship('Shop', back_populates='stock')

    def __str__(self):
        return f'{self.shop.name} ({self.count} pcs.)'


class Sale(Base):
    __tablename__ = 'sale'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    date_sale = sqlalchemy.Column(sqlalchemy.DateTime)
    id_stock = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("stock.id"), nullable=False)
    count = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)

    def __str__(self):
        return f'${self.price} ({self.count} pcs.) till {self.date_sale}'


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
