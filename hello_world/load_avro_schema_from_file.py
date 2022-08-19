from confluent_kafka import avro


def load_avro_schema_from_file(schema_file):
    value_schema = avro.load(schema_file)

    return value_schema
