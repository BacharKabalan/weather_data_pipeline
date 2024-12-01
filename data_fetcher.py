import requests
import time
import yaml
from kafka import KafkaProducer
import json
import asyncio


#Load configuration
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Validate interval
interval = config['api']['interval']
if not isinstance(interval, (int, float)) or interval <= 0:
    raise ValueError(f"Invalid interval value: {interval}")

#Initiate kafak producer - this allows to send messages to the Kafka cluster
for _ in range(5):  # Retry up to 5 times
    try:
        producer = KafkaProducer(
        bootstrap_servers=config['kafka']['bootstrap_servers'],
        api_version=(2, 8, 1),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Kafka producer initialized successfully!")
        break
    except Exception as e:
        print(f"Retrying Kafka connection: {e}")
        time.sleep(5)
else:
    raise Exception("Failed to connect to Kafka after retries.")

#Define the function that will continuously send kafka messages
async def fetch_weather_data():
    while True:
        print("Fetching weather data...")
        #Define the parameters that will be used when requesting data from the openweathermap API 
        params = {
            'q':config['api']['city'],
            'appid': config['api']['key']
            }
        try:
            response = requests.get(config['api']['url'], params=params)
            if response.status_code == 200:
                data = response.json()
                producer.send(config['kafka']['topic'], value=data)
                print("Data sent to Kafka:", data)
            else:
                print("Failed to fetch data. Status code:", response.status_code)
        except Exception as e:
            print(f"Error during data fetching or sending: {e}")

        # try:
        #     time.sleep(interval)
        # except KeyboardInterrupt:
        #     print("Script interrupted by user. Exiting...")
        #     break  # Exit the loop gracefully

        # Wait asynchronously for the specified interval
        await asyncio.sleep(config['api']['interval'])
# Run the async function
async def main():
    try:
        await fetch_weather_data()
    except Exception as e:
        print(f"Unhandled exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())



# if __name__ == "__main__":

#     try:
#         fetch_weather_data()
#     except Exception as e:
#         print(f"Unhandled exception: {e}")

