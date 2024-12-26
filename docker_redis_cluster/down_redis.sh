#!/bin/bash

# Exit script if any command fails
set -e

# Define the data folder to be removed
DATA_FOLDER="./data"

# Stop Docker Compose services
echo "Stopping Redis cluster containers..."
docker-compose down

# Remove any remaining containers with names that match redis_node_*
echo "Removing any residual Redis cluster containers..."
docker rm -f redis_node_1 redis_node_2 redis_node_3 || true

# Remove the Redis cluster network
echo "Removing Redis cluster network..."
docker network rm 3node_m_redis-cluster-net || true

# Remove the Redis data folder
if [ -d "$DATA_FOLDER" ]; then
    echo "Removing Redis data folder: $DATA_FOLDER..."
    sudo rm -rf "$DATA_FOLDER"
    echo "Data folder removed successfully."
else
    echo "Data folder does not exist, skipping removal."
fi

echo "Redis cluster has been successfully stopped, cleaned up, and data folder removed."
