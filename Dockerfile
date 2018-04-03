FROM sd2e/reactors:python2-edge

RUN mkdir -p /schemas
ADD data-representation/manifest/schemas/manifest_schema.json /schemas/manifest_schema.json

# The reactors library can automatically validate JSON messages against
# one or more defined JSON schemas
ADD message.jsonschema /
# For use with 'make tests'
ADD tests /tests
