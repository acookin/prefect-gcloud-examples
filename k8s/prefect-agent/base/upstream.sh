#!/bin/bash

HELM_REPO="https://prefecthq.github.io/prefect-helm/"
HELM_VERSION="2022.12.22"
HELM_CHART="prefect-agent"
NAMESPACE=prefect

helm template \
    --repo ${HELM_REPO} \
    --version ${HELM_VERSION} \
    --namespace ${NAMESPACE} \
    --values ./values.yaml \
    prefect-agent \
    prefect-agent > upstream.yaml
