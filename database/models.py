from sqlalchemy import BigInteger, ForeignKey, Numeric, String, Text, Float, DateTime, func, Integer, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):    
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(),onupdate=func.now())


# class Banner(Base):
#     __tablename__ = 'banner'

#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     name: Mapped[str] = mapped_column(String(15), unique=True)
#     image: Mapped[str] = mapped_column(String(150), nullable=True)
#     description: Mapped[str] = mapped_column(Text, nullable=True)
    
class Category(Base):
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)



class Item(Base):
    __tablename__ = 'item'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    image: Mapped[str] = mapped_column(String(150))
    category_id: Mapped[int] = mapped_column(ForeignKey('category.id', ondelete='CASCADE'), nullable=False)

    category: Mapped['Category'] = relationship(backref='item') 
    

class Prices(Base):
    __tablename__ = 'prices'

    id:Mapped[int] = mapped_column(primary_key=True, autoincrement=True)    
    item_id:Mapped[int] = mapped_column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    count:Mapped[int] = mapped_column(Integer(),nullable=False)
    price:Mapped[float] = mapped_column(Float(asdecimal=True),nullable=False)

    item: Mapped['Item'] = relationship(backref='prices') 

class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str]  = mapped_column(String(150), nullable=True)
    phone: Mapped[str]  = mapped_column(String(13), nullable=True)

class Cart(Base):
    __tablename__ = 'cart'    

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    count:Mapped[int] = mapped_column(Integer())    
    price:Mapped[float] = mapped_column(Float(asdecimal=True),nullable=False)

    user: Mapped['User'] = relationship(backref='cart')
    item: Mapped['Item'] = relationship(backref='cart')

#Переделать базу данных
class Order(Base):
    __tablename__ = 'order'    

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)    
    user_id: Mapped[int] = mapped_column(ForeignKey('user.user_id', ondelete='CASCADE'), nullable=False)
    address: Mapped[str] = mapped_column(Text)
    delivery_type: Mapped[str] = mapped_column(Text)
    track_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id', ondelete='CASCADE'), nullable=False)
    count:Mapped[int] = mapped_column(Integer())    
    price:Mapped[float] = mapped_column(Float(asdecimal=True),nullable=False)

    user: Mapped['User'] = relationship(backref='order')
    item: Mapped['Item'] = relationship(backref='order')