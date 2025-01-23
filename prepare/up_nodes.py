from fabric import Connection
from sqlalchemy import create_engine, Column, String, inspect, Boolean, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base
import config

engine = create_engine(f'mysql+pymysql://{config.DATA_BASE_CONNECTION}', echo=True)
inspector = inspect(engine)
Base = declarative_base()
Session = sessionmaker(bind=engine)


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


remote_user = "root"


def up_node(ip, password):
    try:

        #устанавливаем и настраиваем wg

        c = Connection(host=ip, user=remote_user, connect_kwargs={"password": password})

        print('Подключился, начинаю подготовку')

        c.run("sudo apt update")
        c.run("sudo apt install wireguard -y")
        c.run("cd /etc/wireguard/")

        c.run("wg genkey | tee /etc/wireguard/server_privatekey | wg pubkey | tee /etc/wireguard/server_publickey")
        wg_genkey = (c.run("cat server_privatekey", hide=True)).stdout.strip()
        wg_pubkey = (c.run("cat server_publickey", hide=True)).stdout.strip()

        c.run("sudo touch wg0.conf")

        config_content = f"""
        [Interface]
        PrivateKey = {wg_genkey}
        Address = {ip}
        ListenPort = 51821
        PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
        PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
        """

        c.run(f"sudo echo '{config_content}' > wg0.conf", pty=True)

        c.run('echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf')
        c.run("sysctl -p")
        c.run("systemctl enable wg-quick@wg0.service")
        c.run("systemctl start wg-quick@wg0.service")

        #создаем конфиги для wg

        c.run("mkdir /root/config/")

        for i in range(1, config.QUANTITY_OF_CONFIGS):

            c.run(
                f"wg genkey | tee /etc/wireguard/user{i}_privatekey | wg pubkey | tee /etc/wireguard/user{i}_publickey")

            # Чтение публичного ключа клиента
            public_key_client = c.run(f"cat /etc/wireguard/user{i}_publickey", hide=True).stdout.strip()
            private_key_client = c.run(f"cat /etc/wireguard/user{i}_privatekey", hide=True).stdout.strip()

            c.run(f"mkdir /root/config/user{i}")

            # делем файл для подлкючения в конфигу
            c.run(f"echo '[Peer]' > /root/config/user{i}/config_to_add.conf")
            c.run(f"echo 'PublicKey = {public_key_client}' >> /root/config/user{i}/config_to_add.conf")
            c.run(f"echo 'AllowedIPs = 10.1.1.{i}/32' >> /root/config/user{i}/config_to_add.conf")

            # конфига для клиента
            c.run(f"echo '[Interface]' > /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'PrivateKey = {private_key_client}' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'Address = 10.1.1.{i}' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'DNS = 8.8.8.8' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo '' >> /root/config/user{i}/config_to_client.conf")  # Пустая строка для разделения блоков
            c.run(f"echo '[Peer]' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'PublicKey = {wg_pubkey}' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'Endpoint = {ip}:51821' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'AllowedIPs = 0.0.0.0/0' >> /root/config/user{i}/config_to_client.conf")
            c.run(f"echo 'PersistentKeepalive = 20' >> /root/config/user{i}/config_to_client.conf")

            print(f'Конфигурация {i} готова')

        print('Done all')

        c.close()

    except Exception as e:
        print(e)


with Session() as session:
    nodes = session.query(Nodes).all()

    for node in nodes:
        ip = node.ip
        password = node.password
        up_node(ip, password)
        node_name = node.node_name
        for i in range(1, config.QUANTITY_OF_CONFIGS):
            new_record = Configs(
                node_name=node_name,
                config_number=i,
                available=True
            )
            session.add(new_record)

    session.commit()
