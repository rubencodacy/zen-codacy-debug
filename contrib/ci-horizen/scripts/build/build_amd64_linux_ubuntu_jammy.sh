#!/bin/bash

set -euo pipefail

docker run --rm -v "${TRAVIS_BUILD_DIR}:/mnt/build" -v "$HOME/.ccache:/mnt/.ccache" -e LOCAL_USER_ID="$(id -u)" \
  -e LOCAL_GRP_ID="$(id -g)" --env-file <(env | grep 'DOCKER_\|MAKEFLAGS\|SONAR_CLOUD_FLAG') "${IMAGE_NAME}:${IMAGE_TAG}" \
  bash -c 'set -xeuo pipefail && export HOST="$(gcc -dumpmachine)" && export SONAR_CLOUD_FLAG="${SONAR_CLOUD_FLAG:-}" \
    && export MAKEFLAGS="${MAKEFLAGS:-} -j $(($(nproc)+1))" \
    && cd "${DOCKER_HOME}" && /usr/bin/time -v ./zcutil/build.sh ${SONAR_CLOUD_FLAG} $MAKEFLAGS'
