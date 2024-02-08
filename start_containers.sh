#!/bin/bash

# Directory inside Docker container
DOCKER_DIR="/app/storage"

# Directory on the host machine for backup
HOST_DIR="../storage-backup"

# Name of the Docker container
CONTAINER_NAME="backend-tp-backendtp-1"

start_containers() {
    docker-compose up
}

# Function to synchronize files from Docker container to host machine
sync_files() {
    while true; do
        # Get current date and time
        current_time=$(date +"%Y-%m-%d %T")

        # Get the current working directory
        current_directory=$(pwd)

        # Log the current date, time, and current directory
        echo "Syncing files at $current_time from $DOCKER_DIR to $HOST_DIR in $current_directory"

        # Use rsync to synchronize new files from Docker directory to host directory
        docker cp "$CONTAINER_NAME:$DOCKER_DIR/." "$HOST_DIR/"

        # Sleep for 1 minute
        sleep 60
    done
}

# Permission
chmod +x "$0"

# Check if directory exists; if not, create it
if [ ! -d "$HOST_DIR" ]; then
    mkdir -p "$HOST_DIR"
    echo "Created directory: $HOST_DIR"
else
    echo "Directory already exists: $HOST_DIR"
fi

# Start containers in the background
start_containers &

# Synchronize files from Docker container to host machine in the background
sync_files &

# Wait for both processes to finish
wait
