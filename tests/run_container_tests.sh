#!/usr/bin/env bash

COMMANDS="$@"

if [ -f "reactor.rc" ]; then
    source reactor.rc
else
    echo "Missing reactor ini file"
fi

CONTAINER_IMAGE="$DOCKER_HUB_ORG/${DOCKER_IMAGE_TAG}:${DOCKER_IMAGE_VERSION}"

if [ -z "${CONTAINER_IMAGE}" ]; then
    echo "Usage: $(basename $0) <container_image>" &&
    exit 1
fi

MOUNTS="-v ${PWD}:/mnt/ephemeral-01"
if [ -d "${HOME}/.agave" ]; then
    MOUNTS="$MOUNTS -v ${HOME}/.agave:/root/.agave:rw"
fi

docker run -it ${MOUNTS} ${CONTAINER_IMAGE} ${@}
