from pyflink.datastream import StreamExecutionEnvironment, TimeCharacteristic # Importing the Flink streaming execution environment to set up the job.
from pyflink.datastream.connectors import FlinkKafkaConsumer # Importing Kafka consumer for ingesting data from a Kafka topic.
from pyflink.datastream.connectors import FlinkKafkaProducer # Importing Kafka producer for sending processed data back to another Kafka topic.
from pyflink.common.serialization import SimpleStringSchema # Schema for simple string serialization and deserialization.
from pyflink.datastream.window import Time # Importing time windowing functionality for streaming aggregation.
import json # Importing JSON library for parsing incoming weather data.
import requests # Importing requests library to send HTTP requests to InfluxDB.
from pyflink.common import Configuration


#kafka and influxDB configuration
KAFKA_BROKER = 'kafka:9092' #kafka broker address
KAFKA_INPUT_TOPIC = 'weather_data'# input kafka topic name for raw weather data
KAFKA_OUTPUT_TOPIC = 'aggregated_weather_data'#output kafka topic for aggregated weather data

INFLUXDB_URL = 'http://influxdb:8086'#influx db address
INFLUXDB_TOKEN = 'VRJTWKoPsBgslU2sWskDY86CxfVeC0hcFGoKYIP_013bVjraesGvHkDjsIDYAY4y7r5lYW5vvy6ACh80mpdRvg=='#athentification token for influxdb
INFLUXDB_ORG = 'weather_data'#influxdb organisation name
INFLUXDB_BUCKET = 'weather'#influxdb bucket name




#helper function to write data to influxDB
def write_to_influxdb(data):
    #define http headers for influxdB API
    headers = {"Authorization": f"Token {INFLUXDB_TOKEN}",
               "Content-Type": "text/plain"
               }
    #construct the influxDB write API endpoint
    url = f"{INFLUXDB_URL}/api/v2/write?org={INFLUXDB_ORG}&bucket={INFLUXDB_BUCKET}&precision=s"

    #send the data to influxDB
    response = requests.post(url,headers=headers,data=data)

    if response.status_code != 204:
        print(f"Failed to write to influxDB: {response.status_code}, {response.text}")

#flink job
def main():
    #set the python interpreter path
    global_job_parameters = {
    "python.executable": "/usr/bin/python3"
    }
    #set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.get_config().set_global_job_parameters(global_job_parameters)
    #configure the time characteristic to processing time
    env.set_stream_time_characteristic(TimeCharacteristic.ProcessingTime)
    #set the parallelism level for the flink job 
    env.set_parallelism(1)

    #kafka consumer
    consumer = FlinkKafkaConsumer(
        topics = KAFKA_INPUT_TOPIC, #subscribe to the input kafka topics
        deserialization_schema = SimpleStringSchema(), #deserialize messages as simple strings
        properties = {'bootstrap.servers': KAFKA_BROKER} #kafka broker connection properties
    )

    #kafka producer
    producer = FlinkKafkaProducer(
        topic = KAFKA_OUTPUT_TOPIC, # publish processed data to the output kafka topic
        producer_config = {'bootstrap.servers': KAFKA_BROKER}, #kafka broker connection properties
        serialization_schema = SimpleStringSchema() #serialize messages as simple strings
    )
    
    #ingest weather data
    stream = env.add_source(consumer) # add the kafka consumer as a data source

    #Process weather data: extract, calculate and aggregate

    def process_weather_data(raw_data):
        #parse incoming json data, extract weather details and calculate heat index
        try:
            data = json.loads(raw_data)
            temp = data['main']['temp']
            humidity = data['main']['humidity']
            city = data.get('name','Unknown')

            #calculate the heat index 
            heat_index = temp + 0.5 * (humidity/100.0 * temp - temp)

            #format data for influxdb
            influx_data = f"weather,city={city} temperature={temp}, humidity={humidity},heat_index={heat_index}"
            write_to_influxdb(influx_data)

            #return a formatted string for kafka output
            return f"{city}: Temp={temp}, Humidity={humidity}, Heat Index={heat_index}"
        except Exception as e:
            #log errors
            print(f"Error processing data: {e}")
            return ""

    processed_stream = stream.map(process_weather_data)

    
    #output processed data
    processed_stream.add_sink(producer) #send processed data to the kafka producer

    #execute the flink pipeline
    env.execute("Enhanced Weather Data Processor")

if __name__ == "__main__":
    main() # run the flink job