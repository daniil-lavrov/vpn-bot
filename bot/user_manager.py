from datetime import datetime
from sqlalchemy import create_engine, Column, BigInteger, String, inspect, Boolean, Integer, distinct, \
    DateTime, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import random
import config
import aiohttp
import io

# Создаём таблицы, если их нет - users, clusters и cluster_1

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

class Ads(Base):
    __tablename__ = 'ads'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(350))
    times_shown = Column(Integer)
    available = Column(Boolean)


class User_manager:

    @staticmethod
    async def get_ads_text(chat_id):
        with Session() as session:
            try:
                # Выборка строк из таблицы Ads, где available = True
                available_ads = session.query(Ads).filter(Ads.available == True).all()

                # Выбор случайных 3-х строк
                random_ads = random.sample(available_ads, min(3, len(available_ads)))

                # Объединение текста в одну переменную
                combined_text = '\n\n'.join(ad.text for ad in random_ads)

                # Увеличение times_shown на 1 для каждой из выбранных записей
                for ad in random_ads:
                    ad.times_shown += 1

                user = session.query(Users).filter_by(chat_id=chat_id).first()

                user.last_ads = datetime.now()
                user.status = 'active'

                # Сохранение изменений в базе данных

                user = session.query(Users).filter_by(chat_id=chat_id).first()

                answer = User_manager.api_unfroze(f"{user.node_name}/{str(user.config_num)}")

                if answer == 'error_repeat':
                    session.rollback()
                    return 'error_repeat'
                else:
                    session.commit()
                    return combined_text

            except:
                session.rollback()
                return 'error_repeat'


    @staticmethod
    async def api_unfroze(path):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://backend/unfroze/{path}') as response:
                    if response.status == 200:
                        pass
                    else:
                        return 'error_repeat'
        except:
            return 'error_repeat'


    @staticmethod
    async def api_get_config(path):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://backend/get_config/{path}') as response:
                    if response.status == 200:
                        # Создаем объект BytesIO для хранения данных файла
                        file_content = io.BytesIO(await response.read())
                        # Перемещаем указатель потока в начало
                        file_content.seek(0)
                        return file_content
                    else:
                        return 'error_repeat'
        except:
            return 'error_repeat'


    @staticmethod
    async def create_user(chat_id):
        with Session() as session:
            try:
                user = session.query(Users).filter_by(chat_id=chat_id).first()

                if user is None:

                    config = session.query(Configs).filter_by(available=True).first()

                    if config is None:
                        new_user = Users(
                            chat_id=chat_id,
                            node_name='-',
                            config_num=0,
                            status='inactive'
                        )

                        session.add(new_user)
                        session.commit()

                        return 'no_available_config'

                    else:

                        answer = await User_manager.api_unfroze(f"{config.node_name}/{str(config.config_num)}")
                        if answer == 'error_repeat':
                            return 'error_repeat'

                        new_user = Users(
                            chat_id=chat_id,
                            node_name=config.node_name,
                            config_num=config.config_num,
                            status='active'
                        )

                        config.available = False

                        session.add(new_user)
                        session.commit()

                        return True

                else:

                    return False

            except Exception:
                session.rollback()
                return 'error_repeat'

    @staticmethod
    async def get_link_config(chat_id):
        with Session() as session:
            # вернет либо ссылку на конфигу, либо еррор репит, либо no_available_config
            try:
                user = session.query(Users).filter_by(chat_id=chat_id).first()
                if user.status == 'inactive':
                    config = session.query(Configs).filter_by(available=True).first()
                    if config is None:
                        return 'no_available_config'
                    else:
                        user.node_name = config.node_name
                        user.config_num = config.config_num
                        config.available = False
                        session.commit()
                        return 'go_to_status_to_unfroze'
                elif user.status == 'active':
                    return f'{user.node_name}/{str(user.config_num)}'

            except Exception:
                session.rollback()
                return 'error_repeat'

    @staticmethod
    async def get_status(chat_id):
        with Session() as session:
            try:
                user = session.query(Users).filter_by(chat_id=chat_id).first()
                return user.status
            except:
                return 'error_repeat'

    @staticmethod
    async def check_config_owner(chat_id, path):
        with Session() as session:
            try:
                user = session.query(Users).filter_by(chat_id=chat_id).first()
                if (user.node_name + "/" + str(user.config_num)) == path:
                    return True
                else:
                    return False
            except Exception:
                session.rollback()
                return 'error_repeat'

