#!/bin/bash

# Exit script if any command fails
set -e

# Start Docker Compose
docker-compose up -d

# Wait for Redis containers to initialize
echo "Waiting for Redis containers to start..."
sleep 5

# Get the IPs of Redis containers
NODE1_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q redis-node-1))
NODE2_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q redis-node-2))
NODE3_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q redis-node-3))

echo "Node 1 IP: $NODE1_IP:6379"
echo "Node 2 IP: $NODE2_IP:6379"
echo "Node 3 IP: $NODE3_IP:6379"

# Initialize the Redis Cluster
echo "Initializing Redis Cluster..."
#!/bin/bash

# Exit script if any command fails
set -e

# Start Docker Compose
docker-compose up -d

# Wait for Redis containers to initialize
echo "Waiting for Redis containers to start..."
sleep 5

# Get the IPs of Redis containers
NODE1_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q redis-node-1))
NODE2_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q redis-node-2))
NODE3_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $(docker-compose ps -q redis-node-3))

echo "Node 1 IP: $NODE1_IP:6379"
echo "Node 2 IP: $NODE2_IP:6379"
echo "Node 3 IP: $NODE3_IP:6379"

# Initialize the Redis Cluster with authentication
echo "Initializing Redis Cluster..."
docker exec -it $(docker-compose ps -q redis-node-1) redis-cli -a 'password' --cluster create $NODE1_IP:6379 $NODE2_IP:6379 $NODE3_IP:6379 --cluster-replicas 0

echo "Redis Cluster has been successfully initialized."


echo "Redis Cluster has been successfully initialized."
