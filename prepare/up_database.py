from sqlalchemy import create_engine, Column, BigInteger, String, inspect, Boolean, Integer, DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import config

# Создаём таблицы, если их нет

engine = create_engine(f'mysql+pymysql://{config.DATA_BASE_CONNECTION}', echo=True)
inspector = inspect(engine)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Users(Base):
    __tablename__ = 'users'

    chat_id = Column(BigInteger, unique=True, primary_key=True)
    node_name = Column(String(10))
    config_num = Column(Integer)
    status = Column(String(10))
    last_ads = Column(DateTime, default=func.now(), nullable=False)


class Configs(Base):
    __tablename__ = 'configs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_name = Column(String(10))
    config_num = Column(Integer)
    available = Column(Boolean)


class Nodes(Base):
    __tablename__ = 'nodes'

    node_name = Column(String(10), primary_key=True)
    ip = Column(String(20))
    password = Column(String(50))

class Ads(Base):
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(350))
    times_shown = Column(Integer)
    available = Column(Boolean)


if not inspector.has_table('users'):
    Base.metadata.create_all(engine)

if not inspector.has_table('configs'):
    Base.metadata.create_all(engine)

if not inspector.has_table('nodes'):
    Base.metadata.create_all(engine)

if not inspector.has_table('ads'):
    Base.metadata.create_all(engine)