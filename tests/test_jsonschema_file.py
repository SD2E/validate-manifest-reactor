import os
import json
import sys
from jsonschema import validate, RefResolver

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, 'data', 'example-manifest.json')
SCHEMA = '/schemas/manifest_schema.json'


def test_validate_manifest_schema():
    '''Deployed schema validator works against a local file'''
    with open(MANIFEST) as object_file:
        object_json = json.loads(object_file.read())

    with open(SCHEMA) as schema_file:
        schema_json = json.loads(schema_file.read())
        schema_abs = 'file://' + os.path.abspath(SCHEMA)

    class fixResolver(RefResolver):
        def __init__(self):
            RefResolver.__init__(self, base_uri=schema_abs, referrer=None)
            self.store[schema_abs] = schema_json

    try:
        validate(object_json, schema_json, resolver=fixResolver())
        print("Success")
    except Exception as e:
        raise Exception("Exception validating {}".format(MANIFEST), e)
