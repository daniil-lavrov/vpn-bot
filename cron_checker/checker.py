from sqlalchemy import create_engine, Column, String, inspect, Boolean, Integer, DateTime, func, BigInteger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime, timedelta
import config
import aiohttp

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


async with aiohttp.ClientSession() as http_session:
    with Session() as db_session:
        # Извлекаем всех пользователей из таблицы
        users = db_session.query(Users).all()

        for user in users:
            time_now = datetime.now()
            time_difference = time_now - user.last_ads

            path = user.node_name + "/" + str(user.config_num)

            if user.status == 'active':
                if time_difference > timedelta(days=1):
                    async with http_session.get(f'http://backend/froze/{path}') as response:
                        if response.status == 200:
                            user.status = 'frozen'
                            db_session.commit()

            elif user.status == 'frozen':
                if time_difference > timedelta(days=3):
                    async with http_session.get(f'http://backend/refresh/{path}') as response:
                        if response.status == 200:
                            user.status = 'inactive'
                            db_session.commit()



