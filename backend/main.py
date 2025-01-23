from sqlalchemy import create_engine, Column, String, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
from fastapi import FastAPI
from fabric import Connection
from starlette.responses import StreamingResponse
import io
import config

app = FastAPI()

remote_user = "root"

engine = create_engine(f'mysql+pymysql://{config.DATA_BASE_CONNECTION}', echo=True)
inspector = inspect(engine)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class Nodes(Base):
    __tablename__ = 'nodes'

    node_name = Column(String(10), primary_key=True)
    ip = Column(String(20))
    password = Column(String(50))


@app.get("/unfroze/{node_name}/{config_num}")
async def unfroze(node_name: str, config_num: str):
    with Session() as session:
        node = session.query(Nodes).filter_by(node_name=node_name).first()

        c = Connection(host=node.ip, user=remote_user, connect_kwargs={"password": node.password})
        c.run(f"cat /root/config/user{config_num}/config_to_add.conf >> /etc/wireguard/wg0.conf")
        c.run("systemctl restart wg-quick@wg0.service")
        c.close()


@app.get("/froze/{node_name}/{config_num}")
async def froze(node_name: str, config_num: str):
    with Session() as session:
        node = session.query(Nodes).filter_by(node_name=node_name).first()

        c = Connection(host=node.ip, user=remote_user, connect_kwargs={"password": node.password})

        wg_content = c.run(f"cat /etc/wireguard/wg0.conf", hide=True).stdout

        # Считываем содержимое config_to_add.conf
        config_content = c.run(f"cat /root/config/user{config_num}/config_to_add.conf", hide=True).stdout.strip()

        # Парсинг wg0.conf в список блоков
        lines = wg_content.splitlines(keepends=True)  # Сохраняем переводы строк
        blocks = []
        current_block = ''

        for line in lines:
            # Если строка начинается с [Interface] или [Peer], это начало нового блока
            if line.strip().startswith('[Interface]') or line.strip().startswith('[Peer]'):
                if current_block:
                    blocks.append(current_block)
                current_block = line  # Начинаем новый блок
            else:
                current_block += line  # Добавляем строку к текущему блоку
        if current_block:
            blocks.append(current_block)  # Добавляем последний блок

        # Ищем и удаляем блок, совпадающий с содержимым config_to_add.conf
        new_blocks = []
        for block in blocks:
            # Сравниваем блоки без лишних пробелов и переводов строк
            if block.strip() != config_content:
                new_blocks.append(block)
            else:
                pass

        # Формируем новое содержимое wg0.conf
        new_wg_content = ''.join(new_blocks)

        # Записываем обновлённое содержимое обратно в wg0.conf
        c.run(f"echo \"{new_wg_content}\" > /etc/wireguard/wg0.conf")

        # Перезапускаем WireGuard, чтобы применить изменения
        c.run("systemctl restart wg-quick@wg0.service")


@app.get("/get_config/{node_name}/{config_num}")
async def get_config(node_name: str, config_num: str):
    with Session() as session:
        node = session.query(Nodes).filter_by(node_name=node_name).first()

        c = Connection(host=node.ip, user=remote_user, connect_kwargs={"password": node.password})

        # Используем io.BytesIO для хранения данных файла в памяти
        file_obj = io.BytesIO()

        # Загружаем файл в память
        c.get(f"/root/config/user{config_num}/config_to_client.conf", file_obj)

        # Перематываем указатель потока в начало
        file_obj.seek(0)

        c.close()

        # Возвращаем файл как поток
        return StreamingResponse(file_obj, media_type="application/octet-stream",
                                 headers={"Content-Disposition": f"attachment; filename=your_config.conf"})


@app.get("/refresh/{node_name}/{config_num}")
async def refresh(node_name: str, config_num: str):
    with Session() as session:
        node = session.query(Nodes).filter_by(node_name=node_name).first()

        c = Connection(host=node.ip, user=remote_user, connect_kwargs={"password": node.password})

        wg_genkey = (c.run("cat server_privatekey", hide=True)).stdout.strip()
        wg_pubkey = (c.run("cat server_publickey", hide=True)).stdout.strip()

        c.run(f"rm -rf /root/config/user{config_num}")

        c.run(
            f"wg genkey | tee /etc/wireguard/user{config_num}_privatekey | wg pubkey | tee /etc/wireguard/user{i}_publickey")

        # Чтение публичного ключа клиента
        public_key_client = c.run(f"cat /etc/wireguard/user{config_num}_publickey", hide=True).stdout.strip()
        private_key_client = c.run(f"cat /etc/wireguard/user{config_num}_privatekey", hide=True).stdout.strip()

        c.run(f"mkdir /root/config/user{config_num}")

        # делем файл для подлкючения в конфигу
        c.run(f"echo '[Peer]' > /root/config/user{config_num}/config_to_add.conf")
        c.run(f"echo 'PublicKey = {public_key_client}' >> /root/config/user{config_num}/config_to_add.conf")
        c.run(f"echo 'AllowedIPs = 10.1.1.{config_num}/32' >> /root/config/user{config_num}/config_to_add.conf")

        # конфига для клиента
        c.run(f"echo '[Interface]' > /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'PrivateKey = {private_key_client}' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'Address = 10.1.1.{config_num}' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'DNS = 8.8.8.8' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo '' >> /root/config/user{config_num}/config_to_client.conf")  # Пустая строка для разделения блоков
        c.run(f"echo '[Peer]' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'PublicKey = {wg_pubkey}' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'Endpoint = {node.ip}:51821' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'AllowedIPs = 0.0.0.0/0' >> /root/config/user{config_num}/config_to_client.conf")
        c.run(f"echo 'PersistentKeepalive = 20' >> /root/config/user{config_num}/config_to_client.conf")