import psycopg2
import datetime
import config
import mq
from psycopg2 import Error


DBHOST = config.DBHOST
DBPORT = config.DBPORT
DB = config.DB
DBUSER = config.DBUSER
DBPASS = config.DBPASS

waittime_sec_2k = config.waittime_sec_2k
waittime_sec_100k = config.waittime_sec_100k


def get_waittime_sec(amount):
    if amount == "0.000000002":
        print("2k")
        waittime_sec = waittime_sec_2k
        return waittime_sec
    elif amount == "0.000000100":
        print("100k")
        waittime_sec = waittime_sec_100k
        return waittime_sec


def create_tables():
    try:
        connection = psycopg2.connect(user=DBUSER,
                                      # пароль, который указали при установке PostgreSQL
                                      password=DBPASS,
                                      host=DBHOST,
                                      port=DBPORT,
                                      database=DB)
        cursor = connection.cursor()
        create_table_query1 = '''CREATE TABLE IF NOT EXISTS payout
                              (xch_wallet_address TEXT     NOT NULL,
                              ip           TEXT    NOT NULL,
                              amount           TEXT    NOT NULL,
                              datetime TEXT NOT NULL); '''
        create_table_query2 = '''CREATE TABLE IF NOT EXISTS walletref
                              (xch_wallet_address  TEXT  UNIQUE  NOT NULL,
                              refid TEXT UNIQUE NOT NULL); '''
        create_table_query3 = '''CREATE TABLE IF NOT EXISTS refuser
                              (xch_wallet_address TEXT  UNIQUE   NOT NULL,
                              ip           TEXT    NOT NULL,
                              refid           TEXT    NOT NULL,
                              datetime TEXT NOT NULL); '''
        cursor.execute(create_table_query1)
        connection.commit()
        cursor.execute(create_table_query2)
        connection.commit()
        cursor.execute(create_table_query3)
        connection.commit()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")


def insert(table=None, xch_wallet_address=None, ip=None, refid=None, amount=None, datetime=None):
    try:
        # Подключиться к существующей базе данных
        connection = psycopg2.connect(user=DBUSER,
                                      # пароль, который указали при установке PostgreSQL
                                      password=DBPASS,
                                      host=DBHOST,
                                      port=DBPORT,
                                      database=DB)

        cursor = connection.cursor()
        # Выполнение SQL-запроса для вставки данных в таблицу
        if table == "payout":
            data = (xch_wallet_address, ip, amount, datetime)
            insert_query = """ INSERT INTO payout (xch_wallet_address,ip,amount,datetime) VALUES (%s, %s, %s, %s)""" ## New payout
            mq.put_in_queue(msg=xch_wallet_address, key=amount)
        elif table == "walletref":
            data = (xch_wallet_address, refid)
            insert_query = """ INSERT INTO walletref (xch_wallet_address , refid) VALUES (%s, %s)"""
        elif table == "walletref":
            data = (xch_wallet_address, ip , refid, datetime)
            insert_query = """ INSERT INTO refuser (xch_wallet_address, ip, refid, datetime) VALUES (%s, %s, %s, %s)"""
        cursor.execute(insert_query, data)
        connection.commit()
        print("Insert success")
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            print("Соединение с PostgreSQL закрыто")

def select(table=None, wallet=None, ip=None, refid=None, amount=None):
    try:
        connection = psycopg2.connect(user=DBUSER,
                                      password=DBPASS,
                                      host=DBHOST,
                                      port=DBPORT,
                                      database=DB)
        cursor = connection.cursor()
        if table == "check_ip":
            print(table)
            cursor.execute("SELECT datetime FROM payout WHERE ip = %s AND amount = %s ORDER BY datetime DESC LIMIT 1", (ip, amount))
        elif table == "check_wallet":
            print(table)
            cursor.execute("SELECT datetime FROM payout WHERE xch_wallet_address = %s AND amount = %s ORDER BY datetime DESC LIMIT 1", (wallet, amount))
        elif table == "walletref":
            print(table)
            cursor.execute("SELECT ref_id FROM xch_faucet_referral_id WHERE xch_wallet_address = %s", (wallet,))
        elif table == "uniq":
            cursor.execute("SELECT count(distinct xch_wallet_address) FROM payout")
        elif table == "total_claims":
            cursor.execute("SELECT count(xch_wallet_address) FROM payout")
        elif table == "total_payout": ## REDO (DON'T WORK)
            cursor.execute("SELECT sum(paid) FROM xch_faucet ORDER BY datetime DESC")
        record = cursor.fetchone()
    except (Exception, Error) as error:
        print("Ошибка при работе с PostgreSQL", error)
    finally:
        if connection:
            cursor.close()
            connection.close()
            waittime_sec = get_waittime_sec(amount)
            if record == None:
                print("PostgreSQL select NONE")
                now_date = datetime.datetime.now()
                data = {'seconds': 43201, "unlock_date": now_date}
                return data
            elif table == "check_ip":
                now_date = datetime.datetime.now()
                format = '%Y-%m-%d %H:%M:%S'
                datefromdb = record[0]
                print(datefromdb)
                last_ip_usage = datetime.datetime.strptime(datefromdb, format)
                print(last_ip_usage)
                diff_ip_usage = now_date - last_ip_usage
                last_usage_seconds = int(diff_ip_usage.total_seconds())
                unlock_date = last_ip_usage + datetime.timedelta(seconds=waittime_sec)
                data = {'seconds': last_usage_seconds, "unlock_date": unlock_date}
                print("PostgreSQL select check_ip")
                return data

            elif table == "check_wallet":
                now_date = datetime.datetime.now()
                print("now date", now_date)
                format = '%Y-%m-%d %H:%M:%S'
                datefromdb = record[0]
                print("date from db", datefromdb)
                last_ip_usage = datetime.datetime.strptime(datefromdb, format)
                print("last ip usage", last_ip_usage)
                diff_ip_usage = now_date - last_ip_usage
                print("diff ip usage", diff_ip_usage)
                last_usage_seconds = int(diff_ip_usage.total_seconds())
                print("last usage seconds", last_usage_seconds)
                unlock_date = last_ip_usage + datetime.timedelta(seconds=waittime_sec)
                print("unlock date", unlock_date)
                data = {'seconds': last_usage_seconds, "unlock_date": unlock_date}
                print(data)
                print("PostgreSQL select check_wallet")
                return data

            elif record is not None:
                print("PostgreSQL select  IS NOT NONE and table is :" + str(table))
                return record[0]

            else:
                print("Strange shit in select")
                print("PostgreSQL select shit " + str(record[0]) + " and table is " + str(table))
                return record[0]


def payout(wallet=None, ip=None, amount=None):
    amount = f"{amount:.9f}"
    ip_result = select(table="check_ip", ip=ip, wallet=wallet, amount=amount)
    wallet_result = select(table="check_wallet", ip=ip, wallet=wallet, amount=amount)
    print("wallet result", wallet_result)
    ip_result_sec = ip_result['seconds']
    wallet_result_sec = wallet_result['seconds']
    ip_result_unlock_date = ip_result['unlock_date']
    wallet_result_unlock_date = wallet_result['unlock_date']
    now_date_dirty = datetime.datetime.now()
    now_date = now_date_dirty.strftime("%Y-%m-%d %H:%M:%S")
    waittime_sec = get_waittime_sec(amount)
    print("wallet result sec", wallet_result_sec)
    if wallet_result_sec == 43201: # new wallets block
        if ip_result_sec == 43201:
            insert(table="payout", xch_wallet_address=wallet, ip=ip, amount=amount, datetime=now_date)
            print("New ip! New wallet : " + str(wallet))
            return "done",wallet_result_unlock_date
        elif ip_result_sec > waittime_sec:
            insert(table="payout", xch_wallet_address=wallet,ip=ip,amount=amount, datetime=now_date)
            return "done",wallet_result_unlock_date
        elif ip_result_sec < waittime_sec:
            print("New wallet : " +str(wallet) + ". but ip used : " + str(ip))
            return "ip_used",ip_result_unlock_date
    elif wallet_result_sec > waittime_sec and ip_result_sec > waittime_sec: # existing wallets block
                insert(table="payout", xch_wallet_address=wallet, ip=ip, amount=amount, datetime=now_date)
                return "done",wallet_result_unlock_date
    elif wallet_result_sec < waittime_sec: # existing wallets block
                print("Wallet used : " + str(wallet))
                return "wallet_used",wallet_result_unlock_date
    elif ip_result_sec < waittime_sec: # existing wallets block
                print("IP used : " + str(ip))
                return "ip_used",ip_result_unlock_date
    else:
        print("DEBUG DATA - WALLET, ip, amount : " + str(wallet , ip , amount) + "ELSE ERROR")
        return "wait_needed_wallet_used"