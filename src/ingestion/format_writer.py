"""Explicit-schema file IO; CSV requires typed restoration on read."""
import csv
import json
from pathlib import Path

import fastavro
import pyarrow as pa
import pyarrow.parquet as pq


def avro_schema(name, records):
    types = {str: 'string', float: 'double', int: 'long', bool: 'boolean'}
    return {'type': 'record', 'name': name, 'fields': [
        {'name': k, 'type': types[type(v)]} for k, v in records[0].items()]}


def write_json(records, path):
    Path(path).write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')


def read_json(path, schema=None):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_csv(records, path):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def read_csv(path, schema):
    casts = {'string': str, 'double': float, 'long': int}
    with open(path, newline='', encoding='utf-8') as f:
        return [{k: casts[next(x['type'] for x in schema['fields'] if x['name'] == k)](v)
                 for k, v in r.items()} for r in csv.DictReader(f)]


def write_parquet(records, path):
    pq.write_table(pa.Table.from_pylist(records), path, compression='snappy')


def read_parquet(path, schema=None):
    return pq.read_table(path).to_pylist()


def write_avro(records, path, schema):
    with open(path, 'wb') as f:
        fastavro.writer(f, schema, records)


def read_avro(path, schema=None):
    with open(path, 'rb') as f:
        return list(fastavro.reader(f, reader_schema=schema))
