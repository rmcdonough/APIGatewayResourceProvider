#!/bin/bash

cfn validate && \
cfn generate && \
#cp resource-role-granular-permissions.yaml resource-role.yaml && \
cfn submit --dry-run && \
cfn submit
echo