import os
import random
from confluent_kafka import SerializingProducer
import simplejson as json
from datetime import datetime, timedelta
import uuid
import time


LOS_ANGELES_COORDINATES = { "latitude": 34.0522, "longitude": -118.2437 }
SAN_DIEGO_COORDINATES = { "latitude": 32.7157, "longitude": -117.1647 }

# Calculate the movement in increments
LATITUDE_INCREMENT = (SAN_DIEGO_COORDINATES['latitude'] - LOS_ANGELES_COORDINATES['latitude']) / 100
LONGITUDE_INCREMENT = (SAN_DIEGO_COORDINATES['longitude'] - LOS_ANGELES_COORDINATES['longitude']) / 100

# Retrieve Kafka broker connection details from env variables. Default is localhost:9092
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')

# Define Kakfa topic names for different data streams. Default are set.
VEHICLE_TOPIC = os.getenv('VEHICLE_TOPIC', 'vehicle_data')
GPS_TOPIC = os.getenv('GPS_TOPIC', 'gps_data')
TRAFFIC_TOPIC = os.getenv('TRAFFIC_TOPIC', 'traffic_data')
WEATHER_TOPIC = os.getenv('WEATHER_TOPIC', 'weather_data')
EMERGENCY_TOPIC = os.getenv('EMERGENCY_TOPIC', 'emergency_data')

random.seed(42)
start_time = datetime.now()
start_location = LOS_ANGELES_COORDINATES.copy()


def get_next_time():
    global start_time
    start_time += timedelta(seconds=random.randint(30, 60)) # update frequency
    return start_time


def generate_gps_data(device_id, timestamp, vehicle_type='private'):
    return {
        'id': uuid.uuid4(),
        'deviceId': device_id,
        'timestamp': timestamp,
        'speed': random.uniform(0, 40), # km/h
        'direction': 'North-East',
        'vehicleType': vehicle_type
    }


def generate_traffic_camera_data(device_id, timestamp, location, camera_id):
    return {
        'id': uuid.uuid4(),
        'deviceId': device_id,
        'cameraId': camera_id,
        'location': location,
        'timestamp': timestamp,
        'snapshot': 'Base64EncodedString' # if have acutal screenshots, can be a URL or Base64
    }


def generate_weather_data(device_id, timestamp, location):
    return {
        'id': uuid.uuid4(),
        'deviceId': device_id,
        'location': location,
        'timestamp': timestamp,
        'temperation': random.uniform(-5, 26), # Celcius
        'weatherCondition': random.choice(['Sunny', 'Cloudy', 'Rain','Snow']),
        'precipitation': random.uniform(0, 25),
        'windSpeed': random.uniform(0, 100), # percentage
        'airQualityIndex': random.uniform(0, 500), # AQL Value
    }


def generate_emergency_incident_data(device_id, timestamp, location):
    return {
        'id': uuid.uuid4(),
        'deviceId': device_id,
        'incidentId': uuid.uuid4(),
        'type': random.choice(['Accident', 'Fire', 'Medical', 'Police', 'None']),
        'timestamp': timestamp,
        'location': location,
        'status': random.choice(['Active', 'Resolved']),
        'description': 'Description of the incident'
    }

'''
    Since JSON does not support UUID objects natively, this function converts UUIDs to string  before serialization.
    Error is raised if object is not a UUID.
    Purpose is to make all Kafka messages JSON-compatible since downstream consumers of the Kafka.
    This function is used with json.dumps(data, default=json_serializer)
'''
def json_serializer(obj):
    if isinstance(obj, uuid.UUID):
        return str(obj)
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message deliverd to {msg.topic()} [{msg.partition()}]')

'''
    The function publishes JSON-encoded data to Kafka and makes sure the messages are promperly formatted (json_serializer) with the UUID, data is partitioned, delivery of success or failure is tracked with delivery_report, and no messages remain unsent due to buffering. 
    Topic: is the Kafka topic to send the message to
    key: uses the field 'id' which is a UUID for partitioning messages in Kafka
    value: data is converted to JSON
    on_delivery: logs success or failure of message
    flush: forces all buffered messages to be sent to Kafka immediately
'''
def produce_data_to_kafka(producer, topic, data):
    producer.produce(
        topic,
        key=str(data['id']),
        value=json.dumps(data, default=json_serializer).encode('utf-8'), # edge case where the uuid may not be passed correctly
        on_delivery=delivery_report
    )

    producer.flush()



# logs coordinate changes of the vehicle as it moves
def simulate_vehicle_movement():
    global start_location

    # move toward location B
    start_location['latitude'] += LATITUDE_INCREMENT
    start_location['longitude'] += LONGITUDE_INCREMENT

    # adding randomness to simulate road travel
    start_location['latitude'] += random.uniform(-0.0005, 0.0005)
    start_location['longitude'] += random.uniform(-0.0005, 0.0005)

    return start_location


def generate_vehicle_data(device_id):
    location = simulate_vehicle_movement()
    return {
        'id': uuid.uuid4(),
        'deviceId': device_id,
        'timestamp': get_next_time().isoformat(),
        'location': (location['latitude'], location['longitude']),
        'speed': random.uniform(10, 40),
        'direction': 'North-East',
        'make': 'Toyota',
        'model': 'Prius',
        'year': 2023,
        'fuelType': 'Electric'
    }


# produces vehicle information 
def simulate_journey(producer, device_id):
    # True while driver is going from location A to location B
    while True:
        vehicle_data = generate_vehicle_data(device_id)
        gps_data = generate_gps_data(device_id, vehicle_data['timestamp'])
        traffic_camera_data = generate_traffic_camera_data(device_id, vehicle_data['timestamp'], vehicle_data['location'], 'Nikon-Cam1')
        weather_data = generate_weather_data(device_id, vehicle_data['timestamp'], vehicle_data['location'])
        emergency_incident_data = generate_emergency_incident_data(device_id, vehicle_data['timestamp'], vehicle_data['location'])


        if(vehicle_data['location'][0] >= SAN_DIEGO_COORDINATES['latitude']
           and vehicle_data['location'][1] <= SAN_DIEGO_COORDINATES['longitude']):
            print('Vehicle has reached Birmingham. Simulation')
            break


        produce_data_to_kafka(producer, VEHICLE_TOPIC, vehicle_data)
        produce_data_to_kafka(producer, GPS_TOPIC, gps_data)
        produce_data_to_kafka(producer, TRAFFIC_TOPIC, traffic_camera_data)
        produce_data_to_kafka(producer, WEATHER_TOPIC, weather_data)
        produce_data_to_kafka(producer, EMERGENCY_TOPIC, emergency_incident_data)

        time.sleep(5)

    


if __name__ == "__main__":
    producer_config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'error_cb': lambda err: print(f'Kafka error: {err}')
    }
    '''
       SerializingProducer allows messages to be sent to Kafka topic with aynce message handling. It serilizes message before sending. Ideal for structured data streaming.
    '''
    producer = SerializingProducer(producer_config)

    try:
        simulate_journey(producer, 'Vehicle-MatYohannes-1')

    except KeyboardInterrupt:
        print('Simulation ended by the user.')
    except Exception as e:
        print(f'Unexpected Error occurred: {e}')

