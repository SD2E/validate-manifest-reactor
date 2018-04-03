# Manifest Validator

This Reactor will validate an SD2E data manifest using the current version
of the project's JSON schema. At present, it simply reports success via 
a log message and the exit code. 

## Build and deploy

* Run `git clone https://github.com/SD2E/data-representation`
* Customize `reactor.rc`. At minimum, you will need to set your own `DOCKER_HUB_ORG`
* Customize `config.yml` based on the sample file.

## Example message

```json
{
    "Key": "sd2e-community/ingest/transcriptic/example-manifest.json"
}
```

In the present case, we're looking for `Key` in the message because this Reactor is immediately
downstream of our [SQS][1] processing services. `Key` is a bucket root-relative path 
passed along in SQS filesystem notifications.

## Successful execution

```shell
Logs for execution lPpPYxJMaOJk:
[INFO] 2018-01-08T23:53:07Z: Message: {'Key': 'sd2e-community/ingest/testing/biofab/yeast-gates_q0/3/manifest/107795-manifest.json'}
[INFO] 2018-01-08T23:53:07Z: Validating agave://data-sd2e-ingest/sd2e-community/ingest/testing/biofab/yeast-gates_q0/3/manifest/107795-manifest.json
[INFO] 2018-01-08T23:53:12Z: Validation successful
```

[1]: https://aws.amazon.com/sqs/
