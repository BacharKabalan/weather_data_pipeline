from kafka import KafkaConsumer
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import yaml
import json

with open('config.yaml') as f:
    config = yaml.safe_load(f)

#create kafka consumer to read data ingested by kafka
consumer = KafkaConsumer(config['kafka']['topic'], bootstrap_servers = config['kafka']['bootstrap_servers'])
print("Kafka consumer initialized successfully!")

#create influxdb client to save the data in a database
influx_client = InfluxDBClient(url=config['influxdb']['url'], token=config['influxdb']['token'], org=config['influxdb']['org'])
#set up a write_api to write messages immediately to influxDB
write_api = influx_client.write_api(write_options=SYNCHRONOUS) #ensures that each call waits until the data is fully written

#define function to process kafka messages and write them to influxDB
def process_weather_data(): 
    #listen to messages from kafka indefinitely 
    for msg in consumer:
        print(msg.value)
        # decode kafka messages and convert to JSON object
        data = json.loads(msg.value.decode('utf-8'))
        #create an influxDB point object which represents a data record for the weather data
        point = Point("weather").tag("city",config['api']['city']).field("temperature",data['main']['temp']).field("humidity",data['main']['humidity'])
        #write the record to influxDB
        write_api.write(bucket = config['influxdb']['bucket'], record=point)
        print("Data written to InfluxDB:", point)

if __name__ == "__main__":
    process_weather_data()
