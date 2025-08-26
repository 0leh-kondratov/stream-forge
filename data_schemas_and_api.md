# Data Schemas and API

This document outlines the data schemas, Kafka topics, and APIs used for communication between the microservices in the StreamForge ecosystem.

---

## 1. Overview of Kafka-based Communication

The primary method of communication between services is through Kafka. There are two main categories of topics:

1.  **Control Plane Topics**: Used to send commands to services.
2.  **Event & Data Topics**: Used by services to publish their status, events, and processed data.

### 1.1 Control Plane: `queue-control` Topic

This topic is used to send commands to one or more running services. A command is a JSON message that specifies a target service (`queue_id`) and the action to perform.

**Key Fields:**

*   `queue_id` (string): The unique identifier of the target service or workflow. Can be a wildcard (`*`) to target all services.
*   `command` (string): The command to be executed. See the list of commands below.
*   `payload` (object, optional): Additional data required for the command.

**Example Command:**

```json
{
  "queue_id": "loader-ws-btcusdt-1672531200",
  "command": "ping",
  "payload": {}
}
```

**Supported Commands:**

| Command            | Payload                                          | Description                                                                 |
| ------------------ | ------------------------------------------------ | --------------------------------------------------------------------------- |
| `ping`             | `{}`                                             | Checks if the service is alive. The service must respond with a `pong` event. |
| `stop`             | `{}`                                             | Commands the service to stop its current task and terminate gracefully.     |
| `start`            | *(Service-specific)*                             | (Assumed) Tells a service to begin its primary function.                    |
| `simulate-loading` | `{}`                                             | (For `dummy-service`) Instructs the service to send periodic `loading` events. |
| `fail-after`       | `{"seconds": N}`                                 | (For `dummy-service`) Instructs the service to fail after N seconds.        |


### 1.2 Event Plane: `queue-events` Topic

Services publish status updates and lifecycle events to this topic. These events allow other systems (like the Queue Manager or UI) to monitor the state of running processes.

**Key Fields:**

*   `queue_id` (string): The unique identifier of the service publishing the event.
*   `event` (string): The type of event.
*   `timestamp` (string): ISO 8601 timestamp of when the event occurred.
*   `payload` (object, optional): Additional data associated with the event.

**Example Event:**

```json
{
  "queue_id": "loader-ws-btcusdt-1672531200",
  "event": "started",
  "timestamp": "2025-01-15T10:00:00Z",
  "payload": {
    "service_version": "v1.2.0"
  }
}
```

**Common Events:**

| Event         | Payload                               | Description                                                              |
| ------------- | ------------------------------------- | ------------------------------------------------------------------------ |
| `started`     | `{"service_version": "..."}`          | Published when a service starts its main execution loop.                 |
| `pong`        | `{"ping_timestamp": "..."}`           | The response to a `ping` command.                                        |
| `loading`     | `{"progress": 0.5, "details": "..."}` | Indicates the ongoing progress of a long-running task.                   |
| `interrupted` | `{}`                                  | Published when a service stops due to a `stop` command.                  |
| `finished`    | `{}`                                  | Published when a service completes its task successfully.                |
| `error`       | `{"reason": "...", "code": 500}`      | Published when a service encounters a critical error and is terminating. |

---

## 2. Loader Data Schemas

Loaders are responsible for fetching data from external sources (APIs, WebSockets) and publishing it to specific Kafka topics. The data is then consumed by other services like the `arango-connector`.

*(Note: The specific schemas are based on assumptions and should be verified against the loader implementation.)*

### 2.1 Trades Data

*   **Kafka Topic**: `trades`
*   **Description**: Contains individual trade data.
*   **Assumed Schema**:

```json
{
  "exchange": "binance",
  "symbol": "BTCUSDT",
  "trade_id": 123456789,
  "price": 70000.12,
  "quantity": 0.5,
  "timestamp": 1672531200123
}
```

### 2.2 Candles Data

*   **Kafka Topic**: `candles`
*   **Description**: Contains OHLCV (Open, High, Low, Close, Volume) data for a specific time interval.
*   **Assumed Schema**:

```json
{
  "exchange": "binance",
  "symbol": "BTCUSDT",
  "interval": "1m",
  "open_time": 1672531200000,
  "open": 69990.0,
  "high": 70010.5,
  "low": 69985.0,
  "close": 70005.2,
  "volume": 10.5
}
```

---

## 3. ArangoDB Connector Schemas

The `arango-connector` service consumes data from Kafka topics (like `trades` and `candles`) and transforms it into graph structures (vertices and edges) to be stored in ArangoDB.

*(Note: The specific schemas are based on assumptions and should be verified against the connector implementation.)*

### 3.1 Vertex Schema

*   **Description**: Represents entities in the graph, such as a specific trade or a candle.
*   **Assumed Schema**:

```json
{
  "_key": "trade_123456789", // Unique key for the vertex
  "collection": "Trades",    // Target ArangoDB collection
  "data": {
    "price": 70000.12,
    "quantity": 0.5,
    "timestamp": 1672531200123
  }
}
```

### 3.2 Edge Schema

*   **Description**: Represents relationships between vertices.
*   **Assumed Schema**:

```json
{
  "_key": "trade_123_to_candle_456",
  "collection": "TradeBelongsToCandle",
  "_from": "Trades/trade_123456789",
  "_to": "Candles/candle_1m_1672531200000",
  "data": {
    "relationship": "inclusion"
  }
}
```

---

## 4. Service-specific APIs

### 4.1 Prometheus Metrics

Services like `dummy-service` expose a `/metrics` endpoint on port `8000` for Prometheus scraping. This allows for real-time monitoring of the service's health and performance.

**Example Metrics from `dummy-service`:**

```
dummy_events_total{event="started"} 1.0
dummy_events_total{event="pong"} 5.0
dummy_pings_total 5.0
dummy_status_last{status="loading"} 1.0
```
