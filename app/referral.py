import datetime
import uuid
import postgres


def ip_check_sec(ip):
    ip_result = postgres.select(table="check_ip_only", ip=ip)
    if ip_result is not None :
        now_date = datetime.datetime.now()
        last_ip_usage = datetime.datetime.fromisoformat(ip_result)
        diff_ip_usage = now_date - last_ip_usage
        last_ip_usage_seconds = int(diff_ip_usage.seconds)
        return last_ip_usage_seconds
    elif ip_result is None:
        return "9999999"
    else:
        return "error"


def new_refid(wallet):
    wait = True
    while wait is True:
        id = uuid.uuid4().hex[:6].lower()
        data_id = postgres.select(table="walletrefid", refid=id)
        if data_id is None:
            wait = False
            postgres.insert(table="walletref",xch_wallet_address=wallet,refid=id)
            refid_from_wallet = postgres.select(table="walletref",wallet=wallet)
            return refid_from_wallet
        elif data_id is not None:
            wait = True


def check_refid(xch_wallet):
    refid_from_wallet = postgres.select(table="walletref",wallet=xch_wallet)
    print(refid_from_wallet)
    if refid_from_wallet is not None:
        return refid_from_wallet
    elif refid_from_wallet is None:
        data_id = new_refid(xch_wallet)
        return data_id
    else:
        print("Error")
        return "error"