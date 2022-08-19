import uuid
import os

from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer
from munch import Munch
from load_avro_schema_from_file import load_avro_schema_from_file


def lambda_handler(event, context):
    payload = ""
    for record in event['Records']:
        payload = record["body"]

    bootstrap_servers = os.environ['KAFKA_BOOTSTRAP_SERVER']
    schema_registry_url = os.environ['KAFKA_SCHEMA_REGISTRY_URL']
    topic = os.environ['KAFKA_TOPIC']

    schema_registry_conf = {
        'url': schema_registry_url
    }

    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    value_schema = load_avro_schema_from_file("Person.avsc")
    avro_serializer = AvroSerializer(schema_registry_client,
                                     str(value_schema))

    SECURITY_PROTOCOL = "SASL_SSL"
    SASL_MECHANISM = "SCRAM-SHA-512"

    # producer_conf = {'bootstrap.servers': bootstrap_servers,
    #                  'key.serializer': StringSerializer('utf_8'),
    #                  'value.serializer': avro_serializer,
    #                  'ssl.endpoint.identification.algorithm': ' ',
    #                  'sasl.mechanisms': SASL_MECHANISM,
    #                  'security.protocol': SECURITY_PROTOCOL,
    #                  'sasl.username': 'admin',
    #                  'sasl.password': '4dm1n#'}

    producer_conf = {'bootstrap.servers': bootstrap_servers,
                     'key.serializer': StringSerializer('utf_8'),
                     'value.serializer': avro_serializer}

    producer = SerializingProducer(producer_conf)
    print("Producing user records to topic {}. ^C to exit.".format(topic))

    producer.poll(0.0)

    try:
        producer.produce(topic=topic, key=str(uuid.uuid4()), value=payload,
                         on_delivery=delivery_report)
        print("\nFlushing records...")
        producer.flush()
    except Exception as e:
        print("Invalid input, discarding record...")
        raise e


def delivery_report(err, msg):
    """
    Reports the failure or success of a message delivery.
    Args:
        err (KafkaError): The error that occurred on None on success.
        msg (Message): The message that was produced or failed.
    Note:
        In the delivery report callback the Message.key() and Message.value()
        will be the binary format as encoded by any configured Serializers and
        not the same object that was passed to produce().
        If you wish to pass the original object(s) for key and value to delivery
        report callback we recommend a bound callback or lambda where you pass
        the objects along.
    """
    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print('User record {} successfully produced to {} [{}] at offset {}'.format(
        msg.key(), msg.topic(), msg.partition(), msg.offset()))
