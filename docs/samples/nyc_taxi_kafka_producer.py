import io
import json
from datetime import datetime
import avro.schema
import numpy as np
import pandas as pd
import pytz
from avro.io import BinaryEncoder, DatumWriter
from kafka import KafkaProducer
from feathr.utils._env_config_reader import EnvConfigReader

"""
Produce some sample data for streaming feature using Kafka
1. To create topic:
/usr/local/kafka/bin/kafka-topics.sh --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic nyc_driver_test
2. to list all topic:
    /usr/local/kafka/bin/kafka-topics.sh --bootstrap-server=localhost:9092 --list
    /usr/local/kafka/bin/kafka-topics.sh --bootstrap-server=localhost:9092 --describe --topic nyc_driver_test
"""
KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC = "nyc_driver_test"

GENERATION_SIZE = 10


def generate_entities():
    return range(GENERATION_SIZE)


def generate_trips(entities):
    df = pd.DataFrame(columns=["driver_id", "trips_today", "datetime", "created"])
    df["driver_id"] = entities
    df["trips_today"] = range(GENERATION_SIZE)
    df["datetime"] = pd.to_datetime(
        np.random.randint(datetime(2021, 10, 10).timestamp(), datetime(2022, 10, 30).timestamp(), size=GENERATION_SIZE),
        unit="s",
    )
    df["created"] = pd.to_datetime(datetime.now())
    return df


def send_avro_record_to_kafka(topic, record):
    value_schema = avro.schema.parse(avro_schema_json)
    writer = DatumWriter(value_schema)
    bytes_writer = io.BytesIO()
    encoder = BinaryEncoder(bytes_writer)
    writer.write(record, encoder)

    producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)
    producer.send(topic=topic, value=bytes_writer.getvalue())
    producer.flush()


entities = generate_entities()
trips_df = generate_trips(entities)

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

while True:
    # This while loop is used to keep the process runinng and producing data stream;
    # If no need please remove it
    for record in trips_df.drop(columns=["created"]).to_dict("records"):
        print(record)
        record["datetime"] = record["datetime"].to_pydatetime().replace(tzinfo=pytz.utc)
        send_avro_record_to_kafka(topic=KAFKA_TOPIC, record=record)
