from flask import Flask, render_template, redirect, request, session
import datetime, json, mq, postgres, bech32m, geoip2.database
#from flask_recaptcha import ReCaptcha


counters = []


def findgeo(ip=None):
    try:
        with geoip2.database.Reader('static/GeoLite2-Country.mmdb') as reader:
            response = reader.country(ip)
            return response.country.iso_code
    except:
        return 'HZ'


def smart_ads(country=None):
    if country == "RU" or country == "UA" or country == "HZ":
        ad = ''' '''
        return ad
    else:
        ad = ''' '''
        return ad




def counters_upd():
    counters.clear()
    pending2k = mq.get_queue_2k()
    pending100k = mq.get_queue_100k()
    unique_wallets = postgres.select("uniq")
    total_claims = postgres.select(table="total_claims")
    counters.append({"pending2k": pending2k, "pending100k": pending100k,"unique_wallets": unique_wallets, "total_claims": total_claims})
    print("Updating counters")


def encode_address(address=None):
    try:
        bech32m.decode_puzzle_hash(address)
        return "Correct_Address"
    except ValueError:
        return "Invalid_Address"


def clean_sessions():
    print("cleaning sessions")
    if "user_ip" in session:
        session.pop("user_ip")
    if "xch_wallet" in session:
        session.pop("xch_wallet")
    return "ok"


def date():
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return str(date)


postgres.create_tables()
counters_upd()


app = Flask(__name__)
app.secret_key = "lkadjfgkladgljkadlkfglkahdfghadfhgikafg"
app.config.update({'RECAPTCHA_ENABLED': True,
                   'RECAPTCHA_SITE_KEY':
                       '6LfIQ_UaAAAAAJK36p-inzx1ZsXUDdjDZDNmUr1x',
                   'RECAPTCHA_SECRET_KEY':
                       '6LfIQ_UaAAAAAANQ4sweRe5962l4Ad8H3wMzCbC9'})


#recaptcha = ReCaptcha(app=app)


@app.route('/')
def index():
    clean_sessions()
    count_data =json.loads(json.dumps(*counters))
    ip = request.remote_addr
    CN = findgeo(ip=ip)
    ads = smart_ads(country=CN)
    #print(date(), "headers :", request.headers, " USER_IP :", ip)
    session["user_ip"] = ip
    print(date() + " User session begin ip is : " + session["user_ip"])
    return render_template('base.html', gift="true", ads = ads, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])


@app.route('/2k')
def hour():
    clean_sessions()
    count_data = json.loads(json.dumps(*counters))
    ip = request.remote_addr
    session["user_ip"] = ip
    print(date(), "user_agent :", request.headers.get('User-Agent'), " USER_IP :", ip)
    print(date() + " User session begin ip is : " + session["user_ip"])
    return render_template('2k.html', main = "true", total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])


@app.route("/2k", methods=['POST'])
def hour_send(xch_wallet=0):
    ip = request.remote_addr
    count_data = json.loads(json.dumps(*counters))
    form_data = '0'
    xch_wallet = request.form.get('xch_wallet', form_data)
    check_wallet = encode_address(xch_wallet)
    print(date(), "user_agent :", request.headers.get('User-Agent'), " USER_IP :", ip)
    if check_wallet == "Correct_Address":
        print("Address valid")
    elif check_wallet == "Invalid_Address":
        print("Address invalid: " + str(xch_wallet))
        return render_template('wrong_wallet_used.html', total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
    session["xch_wallet"] = xch_wallet
    if "user_ip" in session:
        print(date() + " User ip in 2k session : " + session["user_ip"])
        if xch_wallet == 0:
            print(date() + ' Not works!')
            return render_template('index_error_wrong_wallet.html')
        elif xch_wallet.startswith("xch1") and len(xch_wallet) == 62:
            amount = 0.000000002
            amount_real = 2000
            abuse_check = postgres.payout(wallet=str(xch_wallet), ip=ip, amount=amount)
            print(date() + " 2k abuse check " + str(abuse_check))
            result = abuse_check[0]
            unlock_date = abuse_check[1]
            if result == "ip_used":
                clean_sessions()
                return render_template('ip_used.html',unlock_date = unlock_date, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
            elif result == "wallet_used":
                clean_sessions()
                return render_template('wallet_used.html',unlock_date = unlock_date, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
            elif result == "wait_needed":
                clean_sessions()
                return render_template('wait_needed.html',unlock_date = unlock_date, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
            elif result == "done":
                counters_upd()
                clean_sessions()
                return render_template('sent.html', sent="yes", amount = amount_real, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
            else:
                clean_sessions()
                return render_template('404.html', sent="yes", total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
        else:
            clean_sessions()
            return render_template('wrong_wallet_used.html', total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
    else:
        clean_sessions()
        print(date() + " USER_IP is not in session: " + str(ip))
        return redirect("/")


@app.route('/100k')
def twelve_hour():
    clean_sessions()
    count_data = json.loads(json.dumps(*counters))
    ip = request.remote_addr
    session["user_ip"] = ip
    print(date(), "user_agent :", request.headers.get('User-Agent'), " USER_IP :", ip)
    print(date() + " User 100k session begin ip is : " + session["user_ip"])
    return render_template('100k.html', main = "true", total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])


@app.route("/100k", methods=['POST'])
def twelve_hour_send():
    ip = request.remote_addr
    count_data = json.loads(json.dumps(*counters))
    form_data = '0'
    xch_wallet = request.form.get('xch_wallet', form_data)
    #get_refid = referral.check_refid(xch_wallet)
    session["xch_wallet"] = xch_wallet
    check_wallet = encode_address(xch_wallet)
    print(date(), "user_agent :", request.headers.get('User-Agent'), " USER_IP :", ip)
    if check_wallet == "Correct_Address":
        print("Address valid")
    elif check_wallet == "Invalid_Address":
        print("Address invalid: " + str(xch_wallet))
        return render_template('wrong_wallet_used.html', total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
    if "user_ip" in session:
        xch_wallet = session["xch_wallet"]
        if xch_wallet == 0:
            return render_template('index_error_wrong_wallet.html')
        elif xch_wallet.startswith("xch1") and len(xch_wallet) == 62:
            amount = 0.0000001
            amount_real = 100000
            abuse_check = postgres.payout(wallet=str(xch_wallet), ip=ip, amount=amount)
            print(date() + " 100k abuse check " + str(abuse_check))
            result = abuse_check[0]
            unlock_date = abuse_check[1]
            used_conf = dict(unlock_date=unlock_date, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"] )
            if result == "ip_used":
                clean_sessions()
                return render_template('ip_used.html', **used_conf)
            elif result == "wallet_used":
                clean_sessions()
                return render_template('wallet_used.html', **used_conf)
            elif result == "wait_needed":
                clean_sessions()
                return render_template('wait_needed.html', **used_conf)
            elif result == "done":
                clean_sessions()
                counters_upd()
                return render_template('sent.html', sent="yes", amount = amount_real, total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
            else:
                clean_sessions()
                return render_template('404.html', total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
        else:
            return render_template('wallet_used.html', total_xch_faucet_claims = count_data["total_claims"], total_xch_faucet_users = count_data["unique_wallets"], pending_2k = count_data["pending2k"], pending_100k = count_data["pending100k"])
    else:
        clean_sessions()
        print(date() + " USER_IP is not in session: " + str(ip))
        return redirect("/")

@app.errorhandler(404)
def not_found(e):
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=False,host='0.0.0.0')
