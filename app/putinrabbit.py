import pika
import sqlite3


conn = sqlite3.connect("../config/xch-faucet.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""create table if not exists xch_faucet(xch_wallet_address text, datetime text, ip text, paid text)""")


def uniqe_wallets(type):
    if type == "uniq":
        sql = "SELECT DISTINCT xch_wallet_address FROM xch_faucet ORDER BY xch_wallet_address DESC"
        result = cursor.execute(sql).fetchall()
        for line in result:
            print(line[0])
            put_in_queue(line[0],"gift")

def put_in_queue(msg,key):
    try:
        credentials = pika.PlainCredentials('xch-app', 'HSDcc#$dsa')
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='srv1.crypto-app.ml', credentials=credentials))
        channel = connection.channel()
        channel.exchange_declare(exchange='xch-app-gift', exchange_type='fanout')
        message = msg
        channel.basic_publish(exchange='xch-app-gift', routing_key=key, body=message)
        print(" [x] Sent %r" % message)
        connection.close()
    except:
        print("rabbitmq bad")


print(uniqe_wallets("uniq"))
