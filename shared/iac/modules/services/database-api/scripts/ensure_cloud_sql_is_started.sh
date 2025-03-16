#!/bin/bash

INSTANCE_NAME=$1
PROJECT_ID=$2

if [ -z "$INSTANCE_NAME" ] || [ -z "$PROJECT_ID" ]; then
    echo "Usage: manage_cloud_sql.sh <instance_name> <project_id>"
    exit 1
fi

# Function to get the instance status
get_instance_status() {
    INSTANCE_INFO=$(gcloud sql instances describe "$INSTANCE_NAME" --project "$PROJECT_ID" --format="json" 2>/dev/null)

    # Check if instance does not exist
    if [ -z "$INSTANCE_INFO" ]; then
        echo "NOT_FOUND"
        return
    fi

    ACTIVATION_POLICY=$(echo "$INSTANCE_INFO" | grep -o '"activationPolicy": *"[^"]*"' | awk -F: '{print $2}' | tr -d ' "')
    OPERATION_STATUS=$(gcloud sql operations list \
        --instance="$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --filter="operationType:UPDATE" \
        --sort-by="~startTime" \
        --limit=1 \
        --format="value(status)")

    if [[ "$ACTIVATION_POLICY" == "ALWAYS" && "$OPERATION_STATUS" == "RUNNING" ]]; then
        echo "STARTING"
    elif [[ "$ACTIVATION_POLICY" == "ALWAYS" && "$OPERATION_STATUS" == "DONE" ]]; then
        echo "STARTED"
    elif [[ "$ACTIVATION_POLICY" == "NEVER" && "$OPERATION_STATUS" == "RUNNING" ]]; then
        echo "STOPPING"
    elif [[ "$ACTIVATION_POLICY" == "NEVER" && "$OPERATION_STATUS" == "DONE" ]]; then
        echo "STOPPED"
    else
        echo "UNKNOWN"
    fi
}

INSTANCE_STATUS=$(get_instance_status)
echo "Current instance status: $INSTANCE_STATUS"

case $INSTANCE_STATUS in
    "NOT_FOUND")
        echo "Instance '$INSTANCE_NAME' does not exist in project '$PROJECT_ID'. Doing nothing."
        ;;
    "STARTING")
        echo "Instance is starting. Waiting until it's fully started..."
        while [[ "$(get_instance_status)" == "STARTING" ]]; do
            sleep 5
        done
        echo "Instance has fully started."
        ;;
    "STARTED")
        echo "Instance is already started."
        ;;
    "STOPPING")
        echo "Instance is stopping. Waiting until it's fully stopped..."
        while [[ "$(get_instance_status)" == "STOPPING" ]]; do
            sleep 5
        done
        echo "Instance has fully stopped. Starting the instance..."
        gcloud sql instances patch "$INSTANCE_NAME" --project "$PROJECT_ID" --activation-policy=ALWAYS --quiet
        echo "Waiting until it's fully started..."
        while [[ "$(get_instance_status)" != "STARTED" ]]; do
            sleep 5
        done
        echo "Instance has fully started."
        ;;
    "STOPPED")
        echo "Instance is stopped. Starting the instance..."
        gcloud sql instances patch "$INSTANCE_NAME" --project "$PROJECT_ID" --activation-policy=ALWAYS --quiet
        echo "Waiting until it's fully started..."
        while [[ "$(get_instance_status)" != "STARTED" ]]; do
            sleep 5
        done
        echo "Instance has fully started."
        ;;
    *)
        echo "Unknown instance status. Doing nothing."
        ;;
esac
