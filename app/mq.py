import pika, config

working_queue_2k = config.working_queue_2k
working_queue_100k = config.working_queue_100k
mquser = config.mquser
mqpass = config.mqpass
mqhost = config.mqhost
mqport = config.mqport


def get_queue_2k():
    pika_conn_params = pika.ConnectionParameters(host=mqhost, port=mqport,credentials=pika.credentials.PlainCredentials(mquser, mqpass), )
    connection = pika.BlockingConnection(pika_conn_params)
    channel = connection.channel()
    queue = channel.queue_declare(queue=working_queue_2k, durable=True, exclusive=False, auto_delete=False)
    return queue.method.message_count


def get_queue_100k():
    pika_conn_params = pika.ConnectionParameters(host=mqhost, port=mqport,credentials=pika.credentials.PlainCredentials(mquser, mqpass), )
    connection = pika.BlockingConnection(pika_conn_params)
    channel = connection.channel()
    queue = channel.queue_declare(queue=working_queue_100k, durable=True, exclusive=False, auto_delete=False)
    return queue.method.message_count


def put_in_queue(msg,key):
    if key == "0.000000002":
        try:
            credentials = pika.PlainCredentials(mquser, mqpass)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=mqhost, credentials=credentials))
            channel = connection.channel()
            channel.exchange_declare(exchange=working_queue_2k, exchange_type='fanout')
            message = msg
            channel.basic_publish(exchange=working_queue_2k, routing_key="2000", body=message)
            print(" [x] Sent 2k %r" % message)
            connection.close()
        except:
            print("rabbitmq bad " + str(message))
    elif key == "0.000000100":
        try:
            credentials = pika.PlainCredentials(mquser, mqpass)
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=mqhost, credentials=credentials))
            channel = connection.channel()
            channel.exchange_declare(exchange=working_queue_100k, exchange_type='fanout')
            message = msg
            channel.basic_publish(exchange=working_queue_100k, routing_key="100000", body=message)
            print(" [x] Sent 100k %r" % message)
            connection.close()
        except:
            print("rabbitmq bad " + str(message))