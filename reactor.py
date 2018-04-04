import os
import json
from attrdict import AttrDict
from jsonschema import validate, RefResolver
from reactors.utils import Reactor, agaveutils
# from agave_utils import *
# from agaveutils import *
from agavedb import AgaveKeyValStore

DOWNLOAD_FILE = 'manifest.json'
SCHEMA_FILE = '/schemas/manifest_schema.json'
FS_ROOT = '/tmp'
PWD = os.getcwd()


def validate_file_schema(filename, schema_file=SCHEMA_FILE, permissive=False):
    """
    Validate a JSON document against a JSON schema

    Positional arguments:
    filename - str - path to the JSON file to validate

    Keyword arguments:
    schema_file - str - path to the requisite JSON schema file
    permissive - bool - swallow validation errors [False]
    """
    try:
        with open(filename) as object_file:
            object_json = json.loads(object_file.read())

        with open(schema_file) as schema:
            schema_json = json.loads(schema.read())
            schema_abs = 'file://' + schema_file
    except Exception as e:
        raise Exception("file or schema loading error", e)

    class fixResolver(RefResolver):
        def __init__(self):
            RefResolver.__init__(self, base_uri=schema_abs, referrer=None)
            self.store[schema_abs] = schema_json

    try:
        validate(object_json, schema_json, resolver=fixResolver())
        return True
    except Exception as e:
        if permissive is False:
            raise Exception("file validation failed", e)
        else:
            pass


def validate_json_message(messageJSON='{}',
                          messageschema='/message.jsonschema',
                          permissive=True):
    """
    Validate JSON string against a JSON schema

    Positional arguments:
    messageJSON - str - JSON text

    Keyword arguments:
    schema_file - str - path to the requisite JSON schema file
    permissive - bool - swallow validation errors [False]
    """
    try:
        with open(messageschema) as schema:
            schema_json = json.loads(schema.read())
            schema_abs = 'file://' + messageschema
    except Exception as e:
        raise Exception("schema loading error", e)

    class fixResolver(RefResolver):
        def __init__(self):
            RefResolver.__init__(self, base_uri=schema_abs, referrer=None)
            self.store[schema_abs] = schema_json

    try:
        validate(messageJSON, schema_json, resolver=fixResolver())
        return True
    except Exception as e:
        raise Exception("message validation failed", e)


def main():
    """
    Download and validate a JSON manifest at a given TACC S3 path

    Input message(s):
        {"uri": "s3://storage-system-bucket-alias/path/to/manifest.json"}

    Output message(s):
        {"uri": "s3://storage-system-bucket-alias/path/to/manifest.json"}

    Linked actors:
      - 'copy_dir_s3'
    """

    r = Reactor()
    ag = r.client  # Agave client for grabbing the file
    db = AgaveKeyValStore(ag)
    m = AttrDict(r.context.message_dict)

    r.logger.debug("Config: {}".format(Reactor.settings))
    r.logger.info("Message: {}".format(m))

    s3_uri = m.get('uri')
    agaveStorageSystem, agaveAbsDir, agaveFileName = \
        agaveutils.uri.from_tacc_s3_uri(s3_uri)
    manifestPath = os.path.join('/', agaveAbsDir, agaveFileName)
    sourceAgaveStorageSystem = \
        r.settings.system_maps.get('source').get(agaveStorageSystem)

    r.logger.debug("source-uri: {}".format(
        r.settings.system_maps.get('source').get(agaveStorageSystem)))
    r.logger.debug("storage-system: {}".format(sourceAgaveStorageSystem))
    r.logger.info("validating: {}".format(s3_uri))

    try:
        result = agaveutils.files.agave_download_file(
            agaveClient=ag, agaveAbsolutePath=manifestPath,
            systemId=sourceAgaveStorageSystem, localFilename=DOWNLOAD_FILE)
    except Exception as e:
        r.on_failure(
            "download-faiedl: {}".format(
                agaveutils.uri.to_agave_uri(
                    sourceAgaveStorageSystem, manifestPath)))

    r.logger.info("validating {}".format(result))
    try:
        validate_file_schema(result)
        r.logger.info("validation succeeded")
    except Exception as e:
        r.on_failure("validation failed: {}".format(e))

    # Downstream actions
    #   Trigger S3->POSIX copy via manifest_dir_copy
    #   {"uri": "s3://storage-system-bucket-alias/path/to/manifest.json"}
    if r.local is False:
        try:
            r.logger.info("message: copy_dir_s3")
            mani_dir_copy_id = r.aliases.id_from_alias('copy_dir_s3', db)
            r.logger.info(" copy_dir_s3 id: {}".format(mani_dir_copy_id))
            # Forward original message to the next actor
            mani_dir_copy_msg = m
            r.logger.debug("  message: {}".format(m))
            mani_id = agaveutils.reactors.message_reactor(
                ag, mani_dir_copy_id, mani_dir_copy_msg)
            r.logger.info(" execution: {}".format(mani_id))
        except Exception as e:
            r.logger.error("error initiating copy_dir_s3: {}".format(e))
            if r.settings.linked_reactors.get(
                    'copy_dir_s3').get('ignore_err'):
                pass


if __name__ == '__main__':
    main()
