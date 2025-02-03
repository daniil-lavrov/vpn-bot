import requests
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, inspect, Boolean, Integer, DateTime, func, BigInteger
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from datetime import datetime, timedelta
import config

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

# Создайте фабрику сессий
Session = sessionmaker(bind=engine)

def check_user_status():
    with Session() as db_session:
        try:
            # Извлекаем всех пользователей из таблицы
            users = db_session.query(Users).all()

            for user in users:
                time_now = datetime.now()
                time_difference = time_now - user.last_ads

                path = user.node_name + "/" + str(user.config_num)

                if user.status == 'active':
                    if time_difference > timedelta(days=1):
                        response = requests.get(f'http://backend/froze/{path}')
                        if response.status_code == 200:
                            user.status = 'frozen'
                            db_session.commit()

                elif user.status == 'frozen':
                    if time_difference > timedelta(days=3):
                        response = requests.get(f'http://backend/refresh/{path}')
                        if response.status_code == 200:
                            user.status = 'inactive'
                            user.node_name = '-'
                            user.config_num = 0
                            db_session.commit()

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == '__main__':
    check_user_status()





