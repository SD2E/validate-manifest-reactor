# Manifest Validator

This Reactor will validate an SD2E data manifest using the current version
of the project's JSON schema. It reports success or failure to the unified
logging interface and passes the message along to subsequent steps in the
ETL pipeline.

## Inbound Message(s)

```json
{
    "Key": "s3://sd2e-community/ingest/transcriptic/example-manifest.json"
}
```

Validation for this message is defined in [message.jsonschema]. It is a subset
of [Amazon SQS][1] messaging.

## Actions

This actor expects to communicate with others. The list of aliases can be
found in `config.yml/linked_reactors`. Specifically, on successful validation,
it tells the `copy_dir_s3` actor to migrate the manifest's parent data
directory to project storage for additional ETL actions.

## Output Message(s)

Specification and validation of outbound messages are not yet formally
described, though it should follow a similar form to inbound messages.

```json
{
    "Key": "s3://sd2e-community/ingest/transcriptic/example-manifest.json"
}
```

This outbound format passes along the essential 'Key' field of the message.
It may get decorated with additional metadata.

## Local build and test this Reactor

* Run `git clone https://github.com/SD2E/validate-manifest-reactor`
* Customize `reactor.rc` : Set your own `DOCKER_HUB_ORG`
* Customize `config.yml` based on the sample file
* Customize data in `tests/data` and add/update tests as needed.

### The Makefile

At present, the easiest approach to testing is to use the Makefile, which
relies on the Abaco CLI and a rational configuration of this repo to
perform Pytest-based unit testing inside the destination container.

```
make data-representation
make tests
make clean
```

## Deploy and test

```shell
Logs for execution lPpPYxJMaOJk:
[INFO] 2018-01-08T23:53:07Z: Message: {'Key': 'sd2e-community/ingest/testing/biofab/yeast-gates_q0/3/manifest/107795-manifest.json'}
[INFO] 2018-01-08T23:53:07Z: Validating agave://data-sd2e-ingest/sd2e-community/ingest/testing/biofab/yeast-gates_q0/3/manifest/107795-manifest.json
[INFO] 2018-01-08T23:53:12Z: Validation successful
```

[1]: https://aws.amazon.com/sqs/
