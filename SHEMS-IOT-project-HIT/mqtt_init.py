import socket

nb = 1  # 0- HIT-"139.162.222.115", 1 - open HiveMQ - broker.hivemq.com
brokers = [str(socket.gethostbyname('vmm1.saaintertrade.com')), str(socket.gethostbyname('broker.hivemq.com'))]
ports = ['80', '1883']
usernames = ['MATZI', '']  # should be modified for HIT
passwords = ['MATZI', '']  # should be modified for HIT

broker_ip = brokers[nb]
broker_port = ports[nb]
port = ports[nb]
username = usernames[nb]
password = passwords[nb]

mzs = ['matzi/', '']

sub_topics = [mzs[nb] + '#', '#']
pub_topics = [mzs[nb] + 'test', 'test']

sub_topic = sub_topics[nb]
pub_topic = pub_topics[nb]

# Common
conn_time = 0  # 0 stands for endless loop
topic_prefix = 'pr/home/SHEMS'
manag_time = 10  # sec
topic_alarm = topic_prefix + "alarm"

# SENSORS:
device_id = '1r2v9r5g84g'  # get it on the device sticker on purchase

# Energy consumption thresholds (in kWh)
daily_energy_threshold = 30.0
monthly_energy_threshold = 900.0

# Appliance-specific thresholds (in Watts)
appliance_thresholds = {
    'refrigerator': 150,
    'air_conditioner': 1500,
    'washing_machine': 500,
    'dishwasher': 1200,
    'oven': 2000,
}