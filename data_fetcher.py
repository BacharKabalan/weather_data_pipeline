import requests  # For making API requests to OpenWeatherMap
import time  # For handling retries with sleep
import yaml  # For loading configuration from a YAML file
from kafka import KafkaProducer  # For sending messages to Kafka
import json  # For JSON serialization of data
import asyncio  # For asynchronous operations

# Load configuration from the `config.yaml` file
with open('config.yaml') as f:
    config = yaml.safe_load(f)

# Validate the API interval from the configuration
interval = config['api']['interval']
if not isinstance(interval, (int, float)) or interval <= 0:
    raise ValueError(f"Invalid interval value: {interval}")

# Initialize the Kafka producer
# Retry up to 5 times in case the connection fails
for attempt in range(5):
    try:
        producer = KafkaProducer(
            bootstrap_servers=config['kafka']['bootstrap_servers'],  # Kafka broker address
            api_version=(2, 8, 1),  # Kafka API version
            value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize Python objects to JSON
        )
        print("Kafka producer initialized successfully!")
        break  # Exit the retry loop if initialization is successful
    except Exception as e:
        print(f"Attempt {attempt + 1}: Retrying Kafka connection. Error: {e}")
        time.sleep(5)  # Wait before retrying
else:
    raise Exception("Failed to connect to Kafka after multiple retries.")

# Define an asynchronous function to fetch weather data and send it to Kafka
async def fetch_weather_data():
    """
    Fetch weather data from OpenWeatherMap API and send it to a Kafka topic.
    """
    while True:
        print("Fetching weather data...")

        # Define parameters for the OpenWeatherMap API request
        params = {
            'q': config['api']['city'],  # City name
            'appid': config['api']['key']  # API key
        }

        try:
            # Make a GET request to the API
            response = requests.get(config['api']['url'], params=params)

            # Check if the response status is successful
            if response.status_code == 200:
                data = response.json()  # Parse the JSON response
                producer.send(config['kafka']['topic'], value=data)  # Send the data to Kafka
                print("Data sent to Kafka:", data)
            else:
                print(f"Failed to fetch data. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error during data fetching or Kafka sending: {e}")

        # Wait asynchronously for the specified interval before the next fetch
        await asyncio.sleep(interval)

# Main asynchronous function to manage the weather data fetching process
async def main():
    try:
        await fetch_weather_data()  # Run the weather data fetching process
    except Exception as e:
        print(f"Unhandled exception: {e}")

# Entry point of the script
if __name__ == "__main__":
    asyncio.run(main())  # Start the asynchronous event loop
