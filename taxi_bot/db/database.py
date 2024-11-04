import asyncio
import os
from dotenv import load_dotenv
import asyncmy
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

load_dotenv()
db_url=os.getenv("DATABASE_URL")
Base = declarative_base()

# Класи Driver (Ронанда)
class Driver(Base):
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=False)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    car_images = relationship("CarImage", back_populates='driver')  # Ҷой барои якчанд суратҳои мошинаш (URL ё пайвандҳо)
    
    avr_rating = Column(Float)
    # Муносибат бо DriverPost
    posts = relationship('DriverPost', back_populates='driver')
    
    def __repr__(self):
        return f"<Driver(name='{self.name}', phone_number='{self.phone_number}')>"

# Класи DriverPost (Сафари ронанда)
class DriverPost(Base):
    __tablename__ = 'driver_posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_city = Column(String(50), nullable=False, index=True)
    to_city = Column(String(50), nullable=False, index=True)
    price = Column(Float, nullable=False)
    max_clients = Column(Integer, nullable=False)
    current_clients = Column(Integer, default=0)
    is_online = Column(Boolean, default=True, index=True)
    comment = Column(Text)
    
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    driver = relationship('Driver', back_populates='posts')
    
    # Функсия барои илова кардани мизоҷон ва ҳифзи шумора
    async def add_clients(self, num_clients):
        session = AsyncSessionLocal()
        if self.current_clients + int(num_clients) <= self.max_clients:
            self.current_clients += int(num_clients)
            await session.commit()
        else:
            raise Exception("Шумораи мизоҷон аз ҳадди максимум зиёд мешавад.")
    
    async def minus_clients(self, num_clients):
        session = AsyncSessionLocal()
        self.current_clients -= int(num_clients)
        await session.commit()
        



    def __repr__(self):
        return f"<DriverPost(from_city='{self.from_city}', to_city='{self.to_city}', is_online={self.is_online})>"


class CarImage(Base):
    __tablename__ = 'carimages'

    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id =  Column(String(512))
    driver_user_id = Column(BigInteger, ForeignKey('drivers.user_id'))
    driver = relationship('Driver', back_populates="car_images")


# Класи client
class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone_number = Column(String(20), nullable=False)
    user_id = Column(BigInteger, nullable=False, unique=True, index=True)
    
    ratings = relationship("DriverRating", back_populates="client")
    # Муносибат бо DriverPost
    posts = relationship('ClientPost', back_populates='client')
    
    def __repr__(self):
        return f"<Driver(name='{self.name}', phone_number='{self.phone_number}')>"



# Класи Client (Мизоҷ)
class ClientPost(Base):
    __tablename__ = 'client_posts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    num_clients = Column(Integer, default=1)  # Шумораи мизоҷон (Мизоҷ + Дӯстонаш)
    from_city = Column(String(50), nullable=False, index=True)
    to_city = Column(String(50), nullable=False, index=True)

    client_user_id = Column(BigInteger, ForeignKey('clients.user_id'))
    client = relationship('Client', back_populates='posts')
    

    # Муносибат ба DriverPost (сафари интихобкардаи мизоҷ)
    selected_post_id = Column(Integer, ForeignKey('driver_posts.id'))
    selected_post = relationship('DriverPost')
    
    # Функсия барои интихоби ронанда
    def choose_driver(self, driver_post):
        if driver_post.current_clients + self.num_clients <= driver_post.max_clients:
            driver_post.add_clients(self.num_clients)
        else:
            raise Exception("Шумораи ҷойҳои холии ронанда кофӣ нест.")
    
    def __repr__(self):
        return f"<Client(name='{self.name}', phone_number='{self.phone_number}', num_clients={self.num_clients})>"

# Класи DriverRating (Рейтинг ва коментария барои ронанда)
class DriverRating(Base):
    __tablename__ = 'driver_ratings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rating = Column(Integer)  # Рейтинг аз 1 то 5
    
    client_id = Column(Integer, ForeignKey('clients.id'))
    client = relationship('Client')
    
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    driver = relationship('Driver')
    
    def __repr__(self):
        return f"<DriverRating(rating={self.rating}, driver_id={self.driver_id})>"

# Иҷоди пойгоҳи додаҳо ва алоқа бо SQLite
engine = create_async_engine(db_url, echo=True)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
