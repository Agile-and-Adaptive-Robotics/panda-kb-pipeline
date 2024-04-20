#!/bin/bash

# Script to stop non-essential services

echo "Stopping non-essential services..."

# List of non-essential services
SERVICES=(
  "bluetooth.service"
  "colord.service"
  "cups.service"
  "cups-browsed.service"
  "gdm.service"
  "ModemManager.service"
  "packagekit.service"
  "switcheroo-control.service"
  "kerneloops.service"
)

# Loop through the list of services and stop each one
for SERVICE in "${SERVICES[@]}"; do
  echo "Stopping $SERVICE..."
  sudo systemctl stop "$SERVICE"
  if [ $? -eq 0 ]; then
    echo "$SERVICE stopped successfully."
  else
    echo "Failed to stop $SERVICE. It may not be installed or already stopped."
  fi
done

echo "All specified services have been processed."
