import sys
import random
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDockWidget, QLineEdit, QPushButton, QLabel, QFormLayout, QWidget, QMainWindow, QApplication, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt
import paho.mqtt.client as mqtt
from datetime import datetime
from mqtt_init import *
import json
from icecream import ic
import matplotlib.pyplot as plt
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

update_rate = 5000  # in msec

# MongoDB Connection Setup
uri = "mongodb+srv://smarthomeenergyhit:QcGPTofjyBUsVEov@cluster1.gh8fb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["SmartHomeEnergy"]
collection = db["energy_usage"]

def generate_alarm_topic(device_id, sensor_type):
    return f"{topic_prefix}/{device_id}/alarm/{sensor_type}"

def generate_client_id(device_id):
    return f"IOT_client-SHEMS-Id{device_id}-{random.randrange(1, 10000000)}"

def generate_topic(device_id):
    return f"{topic_prefix}/{device_id}/sts"

def display_number(num):
    return f"{num:.2f}"

def get_simulated_dht_data():
    temp = 22 + random.uniform(1, 10)
    hum = 40 + random.uniform(1, 60)
    return temp, hum

class Mqtt_client():
    def __init__(self):
        self.broker = ''
        self.topic = ''
        self.port = ''
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.subscribeTopic = ''
        self.publishTopic = ''
        self.publishMessage = ''
        self.on_connected_to_form = None
        self.on_disconnected_to_form = None
        self.CONNECTED = False

    def set_on_connected_to_form(self, on_connected_to_form):
        self.on_connected_to_form = on_connected_to_form

    def set_on_disconnected_to_form(self, on_disconnected_to_form):
        self.on_disconnected_to_form = on_disconnected_to_form

    def set_broker(self, broker):
        self.broker = broker

    def set_port(self, port):
        self.port = port

    def set_clientName(self, clientName):
        self.clientname = clientName

    def set_username(self, username):
        self.username = username

    def set_password(self, password):
        self.password = password

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected OK")
            self.CONNECTED = True
            if self.on_connected_to_form:
                self.on_connected_to_form()
        else:
            print(f"Bad connection Returned code={rc}")

    def on_disconnect(self, client, userdata, flags, rc=0):
        self.CONNECTED = False
        if self.on_disconnected_to_form:
            self.on_disconnected_to_form()
        print(f"DisConnected result code {rc}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        print(f"Message from: {topic}, {m_decode}")
        mainwin.subscribeDock.update_mess_win(m_decode)

    def connect_to(self):
        self.client = mqtt.Client(self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        print(f"Connecting to broker {self.broker}")
        self.client.connect(self.broker, self.port)

    def disconnect_from(self):
        self.client.disconnect()

    def start_listening(self):
        self.client.loop_start()

    def stop_listening(self):
        self.client.loop_stop()

    def publish_to(self, topic, message):
        if self.CONNECTED:
            self.client.publish(topic, message)
        else:
            print("Can't publish. Connection should be established first")

    def is_connected(self):
        return self.CONNECTED

class ConnectionDock(QDockWidget):
    def __init__(self, mc):
        QDockWidget.__init__(self)

        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)
        self.mc.set_on_disconnected_to_form(self.on_disconnected)

        self.eDeviceID = QLineEdit()
        self.eDeviceID.setText(device_id)

        self.eConnectBtn = QPushButton("Connect", self)
        self.eConnectBtn.setToolTip("Connect to MQTT Broker")
        self.eConnectBtn.clicked.connect(self.on_button_connect_click)
        self.eConnectBtn.setStyleSheet("background-color: gray")

        self.eCurrentPower = QLineEdit()
        self.eCurrentPower.setText('')

        self.eDailyEnergy = QLineEdit()
        self.eDailyEnergy.setText('')

        self.eMonthlyEnergy = QLineEdit()
        self.eMonthlyEnergy.setText('')

        self.eCurrentTemp = QLineEdit()  # New field for current temperature
        self.eCurrentTemp.setText('')

        self.eTargetTemp = QLineEdit()
        self.eTargetTemp.setText("50")  # Default value of 50°C

        self.tempStatusLabel = QLabel("Temperature looks fine", self)
        self.tempStatusLabel.setAlignment(Qt.AlignCenter)
        self.tempStatusLabel.setFixedHeight(30)  # Shrink the height of the label

        self.relayButton = QPushButton("Relay: OFF", self)
        self.relayButton.setStyleSheet("background-color: lightgray")
        self.relayButton.clicked.connect(self.toggle_relay)

        # Form layout for aligning input fields and labels
        formLayout = QFormLayout()
        formLayout.addRow("Device ID", self.eDeviceID)
        formLayout.addRow("Connect", self.eConnectBtn)
        formLayout.addRow("Current Power (W)", self.eCurrentPower)
        formLayout.addRow("Daily Energy (kWh)", self.eDailyEnergy)
        formLayout.addRow("Monthly Energy (kWh)", self.eMonthlyEnergy)
        formLayout.addRow("Current Temp (°C)", self.eCurrentTemp)  # New row for current temperature
        formLayout.addRow("Max Temp (°C)", self.eTargetTemp)
        formLayout.addRow("Temperature Status", self.tempStatusLabel)
        formLayout.addRow("Relay Control", self.relayButton)

        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setWidget(widget)
        self.setWindowTitle("Smart Home Energy Management System")

        self.relay_on = False  # Variable to track relay status

    def toggle_relay(self):
        if not self.mc.is_connected():
            print("Connect to the broker first.")
            return

        if not self.relay_on:
            self.relayButton.setText("Relay: ON")
            self.relayButton.setStyleSheet("background-color: green")
            self.mc.publish_to("home/relay", "Check the electricity!")
            print("Published: Check the electricity!")
        else:
            self.relayButton.setText("Relay: OFF")
            self.relayButton.setStyleSheet("background-color: lightgray")
            self.mc.publish_to("home/relay", "Problem solved.")
            print("Published: Problem solved.")

        self.relay_on = not self.relay_on

    def on_connected(self):
        self.eConnectBtn.setStyleSheet("background-color: green")
        self.eConnectBtn.setText("Disconnect")

    def on_disconnected(self):
        self.eConnectBtn.setStyleSheet("background-color: red")
        self.eConnectBtn.setText("Connect")

    def on_button_connect_click(self):
        if self.mc.is_connected():
            self.mc.disconnect_from()
        else:
            self.mc.set_broker(broker_ip)
            self.mc.set_port(int(port))
            self.mc.set_clientName(generate_client_id(self.eDeviceID.text()))
            self.mc.set_username(username)
            self.mc.set_password(password)
            self.mc.connect_to()
            self.mc.start_listening()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.mc = Mqtt_client()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_rate)

        self.setGeometry(30, 100, 600, 300)  # Adjusted the window size to give more space
        self.setWindowTitle('Smart Home Energy Management')

        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

        self.daily_energy = 0
        self.monthly_energy = 0
        self.last_update_time = datetime.now()

        # Button to visualize energy usage
        self.visualizeButton = QPushButton("Visualize Energy Usage", self)
        self.visualizeButton.clicked.connect(self.visualize_energy_usage)

        # Button to visualize temperature data
        self.visualizeTempButton = QPushButton("Visualize Temperature Data", self)
        self.visualizeTempButton.clicked.connect(self.visualize_temperature_data)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.visualizeButton)
        layout.addWidget(self.visualizeTempButton)  # Add the visualize button below

        # Create a central widget to hold the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_data(self):
        if not self.mc.is_connected():
            return

        current_time = datetime.now()
        time_diff = (current_time - self.last_update_time).total_seconds() / 3600

        # Simulate electricity usage
        current_power = random.uniform(100, 5000)  # Watts
        energy_consumed = (current_power / 1000) * time_diff

        self.daily_energy += energy_consumed
        self.monthly_energy += energy_consumed

        # Simulate DHT temperature and humidity
        temp, hum = get_simulated_dht_data()

        # Reset daily energy at midnight
        if current_time.date() != self.last_update_time.date():
            self.daily_energy = energy_consumed

        # Reset monthly energy on the first day of the month
        if current_time.month != self.last_update_time.month:
            self.monthly_energy = energy_consumed

        self.last_update_time = current_time

        self.connectionDock.eCurrentPower.setText(display_number(current_power))
        self.connectionDock.eDailyEnergy.setText(display_number(self.daily_energy))
        self.connectionDock.eMonthlyEnergy.setText(display_number(self.monthly_energy))

        # Update the current temperature in the UI
        self.connectionDock.eCurrentTemp.setText(display_number(temp))

        # Get the target temperature entered by the user
        target_temp = float(self.connectionDock.eTargetTemp.text())

        # Check if temperature exceeds the target
        if temp >= target_temp:
            self.connectionDock.tempStatusLabel.setText("Temperature is too high, please check for a power cord that lights up!")
            self.connectionDock.tempStatusLabel.setStyleSheet("color: red")  # Set text color to red

            # Publish an alarm to the alarm topic
            alarm_message = {
                "sensor": "temperature",
                "alarmed_value": temp,
                "time": current_time.isoformat()
            }
            alarm_topic = generate_alarm_topic(self.connectionDock.eDeviceID.text(), "temperature")
            self.mc.publish_to(alarm_topic, json.dumps(alarm_message))
            ic(f"Published alarm to {alarm_topic}: {alarm_message}")
        else:
            self.connectionDock.tempStatusLabel.setText("Temperature looks fine.")
            self.connectionDock.tempStatusLabel.setStyleSheet("color: green")  # Set text color to green

        # Construct message with electricity and temperature data
        message = {
            "current_power": current_power,
            "daily_energy": self.daily_energy,
            "monthly_energy": self.monthly_energy,
            "temperature": temp,
            "humidity": hum,
            "time": current_time.isoformat()
        }

        # Send data to MQTT and MongoDB
        self.send_data(message)
        self.save_to_mongo(message)


    def send_data(self, message):
        msg_json = json.dumps(message)
        topic = generate_topic(self.connectionDock.eDeviceID.text())
        ic(topic, message)
        self.mc.publish_to(topic, msg_json)

    def save_to_mongo(self, message):
        try:
            collection.insert_one(message)
            print("Data logged successfully to MongoDB")
        except Exception as e:
            print(f"Failed to log data: {e}")

    def visualize_energy_usage(self):
        try:
            records = list(collection.find())
        except Exception as e:
            print(f"Failed to retrieve data: {e}")
            return

        if not records:
            print("No data available to visualize")
            return

        timestamps = [datetime.strptime(rec['time'], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d-%m-%Y %H:%M:%S") for rec in records]
        energy_usage = [rec['daily_energy'] for rec in records]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, energy_usage, marker='o')
        plt.title('Energy Usage Over Time')
        plt.xlabel('Time')
        plt.ylabel('Energy Consumed (kWh)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def visualize_temperature_data(self):
        try:
            records = list(collection.find())
        except Exception as e:
            print(f"Failed to retrieve data: {e}")
            return

        if not records:
            print("No temperature data available to visualize")
            return

        # Extract timestamps and temperature values
        timestamps = [datetime.strptime(rec['time'], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d-%m-%Y %H:%M:%S") for rec in records]
        temperatures = [rec['temperature'] for rec in records]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, temperatures, marker='o', color='r')
        plt.title('Temperature Over Time')
        plt.xlabel('Time')
        plt.ylabel('Temperature (°C)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainwin = MainWindow()
    mainwin.show()
    app.exec_()
