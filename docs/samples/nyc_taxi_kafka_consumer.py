import io
import avro.schema
import avro.io
from kafka import KafkaConsumer
import json

"""
Consumer from Kafka
1. To create topic:
/usr/local/kafka/bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic nyc_driver_test
2. to list all topic:
    /usr/local/kafka/bin/kafka-topics.sh --bootstrap-server=localhost:9092 --list
    /usr/local/kafka/bin/kafka-topics.sh --bootstrap-server=localhost:9092 --describe --topic nyc_driver_test

"""
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "nyc_driver_test"

avro_schema_json = json.dumps(
    {
        "type": "record",
        "name": "DriverTrips",
        "fields": [
            {"name": "driver_id", "type": "long"},
            {"name": "trips_today", "type": "int"},
            {"name": "datetime", "type": {"type": "long", "logicalType": "timestamp-micros"}},
        ],
    }
)

def get_avro_record_from_kafka(msg):
    bytes_reader = io.BytesIO(msg.value)
    decoder = avro.io.BinaryDecoder(bytes_reader)
    value_schema = avro.schema.parse(avro_schema_json)
    reader = avro.io.DatumReader(value_schema)
    record = reader.read(decoder)
    print (record)


consumer = KafkaConsumer(KAFKA_TOPIC,
                         bootstrap_servers=[KAFKA_BROKER])

for msg in consumer:
    get_avro_record_from_kafka(msg)


    

