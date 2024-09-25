import paho.mqtt.client as mqtt
import time
import random
from mqtt_init import *
from icecream import ic
from datetime import datetime 

def time_format():
    return f'{datetime.now()}  Manager|> '

ic.configureOutput(prefix=time_format)
ic.configureOutput(includeContext=False)

def on_connect(client, userdata, flags, rc):    
    if rc == 0:
        ic("Connected OK")                
    else:
        ic(f"Bad connection Returned code={rc}")
        
def on_disconnect(client, userdata, flags, rc=0):    
    ic(f"DisConnected result code {str(rc)}")
        
def on_message(client, userdata, msg):
    topic = msg.topic
    m_decode = str(msg.payload.decode("utf-8","ignore"))
    ic(f"Message from: {topic}, {m_decode}")
    
    data = eval(m_decode)
    if data['daily_energy'] > daily_energy_threshold:
        ic(f"Daily energy threshold warning! Current usage: {data['daily_energy']} kWh")
        send_msg(client, topic_alarm, f"Daily energy threshold warning! Current usage: {data['daily_energy']} kWh")
    if data['monthly_energy'] > monthly_energy_threshold:
        ic(f"Monthly energy threshold warning! Current usage: {data['monthly_energy']} kWh")
        send_msg(client, topic_alarm, f"Monthly energy threshold warning! Current usage: {data['monthly_energy']} kWh")

def send_msg(client, topic, message):
    ic(f"Sending message: {message}")    
    client.publish(topic, message)   

def client_init(cname):
    client = mqtt.Client(cname, clean_session=True)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message        
    if username != "":
        client.username_pw_set(username, password)        
    ic(f"Connecting to broker {broker_ip}")
    client.connect(broker_ip, int(port))
    return client

def main():    
    cname = f"Manager-{random.randint(0, 10000)}"
    client = client_init(cname)
    client.loop_start()
    client.subscribe(f"{topic_prefix}/+/sts")
    
    try:
        while True:           
            time.sleep(manag_time)
            ic(f"Time for sleep: {manag_time}")
    except KeyboardInterrupt:
        client.disconnect()
        ic("Interrupted by keyboard")

    client.loop_stop()
    client.disconnect()
    ic("End manager run script")

if __name__ == "__main__":
    main()