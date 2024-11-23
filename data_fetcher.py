import requests
import time
import yaml
from kafka import KafkaProducer
import json


#Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

#Initiate kafak producer - this allows to send messages to the Kafka cluster
producer = KafkaProducer(bootstrap_servers = config['kafka']['bootstrap_servers'])

#Define the function that will continuously send kafka messages
def fetch_weather_data():
    while True:
        #Define the parameters that will be used when requesting data from the openweathermap API 
        params = {
            'q':config['api']['city'],
            'appid': config['api']['key']
            }
        #get the response of the get request
        response = requests.get(config['api']['url'], params=params)

        # check if the request was successful
        if response.status_code == 200: 
            data = response.json() #convert the json response data to a python dictionary

            #send to the Kafka cluster

            producer.send(config['kafka']['topic'], value = json.dumps(data).encode('utf-8'))

            print('Data sent to kafka: ', data)
        else:
            print("Failed to fetch data: ", response.status_code)

        time.sleep(config['api']['interval'])
if __name__ == "__main__":
    fetch_weather_data()

