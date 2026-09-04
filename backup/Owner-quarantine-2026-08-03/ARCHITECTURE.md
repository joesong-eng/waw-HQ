# Owner Project Architecture

This document outlines the architecture of the Owner project, detailing the roles and integration of its components.

## 1. Owner (Sophie) - Core Backend

*   **Type**: Laravel Application
*   **Role**: Core backend for business logic, administration, and user management.
*   **Path**: `/Users/ilawusong/Documents/WaW/Owner/`
*   **Key Components**: Laravel framework, controllers, models, business logic.

## 2. WAW-IOT - Real-time Data Processing Plugin

*   **Type**: Laravel Application (as a submodule/service)
*   **Role**: Handles real-time data ingestion from IoT devices via MQTT, processes revenue events, calculates revenue sharing, and updates machine status.
*   **Path**: `/Users/ilawusong/Documents/WaW/Owner/waw-iot/`
*   **Key Components**:
    *   `MqttListenCommand`: Long-running process to listen to MQTT topics.
    *   `MqttListenerService`: Manages device registration, heartbeat, and event handling.
    *   `RevenueService`: Core logic for calculating revenue shares.
    *   `InternalRevenueController`: Provides an internal API for event processing.
*   **Integration**: Operates as a distinct service within the Owner project. It leverages the same database and shares some models with the core backend. Its lifecycle is managed separately (e.g., running as a daemon).
*   **Relationship**: Acts as a real-time data processing plugin, feeding crucial operational data into the Owner's backend systems.

## 3. Agent Tools

*   **Location**: `/Users/ilawusong/Documents/WaW/Owner/hq_agent_tools/`
*   **Role**: Provides auxiliary tools for agent interaction, such as listeners, reporters, and utilities.
*   **Components**: `agent_listener.py`, `agent_reporter.py`, `db_connector.py`, `mqtt_util.py`, `deploy.sh` (Agent's deployment script).

## 4. Infrastructure Considerations

*   **Database**: Shared across Owner and WAW-IOT. Proper schema management is crucial.
*   **MQTT Broker**: WAW-IOT directly interacts with an MQTT broker.
*   **Redis**: Used by WAW-IOT for storing real-time machine status.

## 5. Development Workflow

*   **Owner Backend**: Standard Laravel development workflow.
*   **WAW-IOT Service**: Run `php artisan mqtt:listen` for real-time data processing.
*   **Dependencies**: Manage PHP dependencies via Composer in the Owner root directory.
*   **Agent Tasks**: Utilize scripts in `hq_agent_tools/` for agent-specific operations.
