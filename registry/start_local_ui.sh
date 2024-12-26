#!/bin/bash

while getopts ":m:p:" opt; do
  case $opt in
    m) mode="$OPTARG"
    ;;
    p) p_out="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    exit 1
    ;;
  esac

  case $OPTARG in
    -*) echo "Option $opt needs a valid argument"
    exit 1
    ;;
  esac
done


printf "Argument mode is %s\n" "$mode"

# Generate static env.config.js for UI app
envfile=/usr/share/nginx/html/env-config.js
echo "window.environment = {" > $envfile

if [[ -z "${REACT_APP_AZURE_CLIENT_ID}" ]]; then
    echo "Environment variable REACT_APP_AZURE_CLIENT_ID is not defined, skipping"
else
    echo "  \"azureClientId\": \"${REACT_APP_AZURE_CLIENT_ID}\"," >> $envfile
fi

if [[ -z "${REACT_APP_AZURE_TENANT_ID}" ]]; then
    echo "Environment variable REACT_APP_AZURE_TENANT_ID is not defined, skipping"
else
    echo "  \"azureTenantId\": \"${REACT_APP_AZURE_TENANT_ID}\"," >> $envfile
fi

if [[ -z "${REACT_APP_ENABLE_RBAC}" ]]; then
    echo "Environment variable REACT_APP_ENABLE_RBAC is not defined, skipping"
else
    echo "  \"enableRBAC\": \"${REACT_APP_ENABLE_RBAC}\"," >> $envfile
fi

echo "}" >> $envfile

echo "Successfully generated ${envfile} with following content"
cat $envfile

# Start nginx
nginx

# Start API app
LISTENING_PORT="8000"

echo "Start SQL registry"
cd /usr/src/registry/sql-registry
nohup uvicorn main:app --host 0.0.0.0 --port $LISTENING_PORT
