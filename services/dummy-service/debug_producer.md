# `debug_producer.py`: Kafka Command Tester for StreamForge

`debug_producer.py` is a CLI tool for sending test commands (`ping`, `stop`) to the Kafka topic `queue-control`, with the option to wait for a `pong` response from `queue-events`.

It is used for debugging StreamForge microservices, primarily `dummy-service`, `loader-producer`, and `arango-connector`.

---

## 1. Key Features

* Send a `ping` command and wait for a `pong` response.
* Send a `stop` command.
* Repeat `ping` commands (`--repeat` mode).
* Measure RTT (round-trip time) between `ping_ts` and `ponged_at`.
* Log sent and received events in JSON format.

---

## 2. Command-Line Arguments

| Argument        | Type             | Description                                                |
| --------------- | ---------------- | ---------------------------------------------------------- |
| `--queue-id`    | str (req.)       | Target queue identifier (e.g., `loader-btcusdt-dummy-...`) |
| `--command`     | `ping` or `stop` | Command to send                                            |
| `--expect-pong` | flag             | Wait for `pong` after `ping` and log delay                 |
| `--repeat`      | int              | Repeat the command `N` times                               |
| `--interval`    | float            | Interval between repeats in seconds (default: `1.0`)       |

---

## 3. Required Environment Variables

`debug_producer.py` connects to Kafka using SASL + TLS.
Set them in `.env` or via `export`:

```dotenv
KAFKA_BOOTSTRAP_SERVERS=k3-kafka-bootstrap.kafka:9093
KAFKA_USER=user-streamforge
KAFKA_PASSWORD=topsecret
KAFKA_CA_PATH=/usr/local/share/ca-certificates/ca.crt

QUEUE_CONTROL_TOPIC=queue-control
QUEUE_EVENTS_TOPIC=queue-events
```

---

## 4. Usage Examples

### 4.1 Send a single `ping` and wait for `pong`

```bash
python3.11 debug_producer.py \
  --queue-id loader-btcusdt-dummy-2024-06-01-testid \
  --command ping \
  --expect-pong
```

### 4.2 Send 5 `ping` commands with 2-second intervals

```bash
python3.11 debug_producer.py \
  --queue-id loader-btcusdt-dummy-2024-06-01-testid \
  --command ping \
  --expect-pong \
  --repeat 5 \
  --interval 2
```

### 4.3 Send a `stop` command

```bash
python3.11 debug_producer.py \
  --queue-id loader-btcusdt-dummy-2024-06-01-testid \
  --command stop
```

---

## 5. Kafka Event Format

### 5.1 Sent (`ping`)

```json
{
  "queue_id": "loader-btcusdt-dummy-2024-06-01-testid",
  "command": "ping",
  "sent_at": 1754202651.997
}
```

### 5.2 Expected from service (`pong`)

```json
{
  "event": "pong",
  "queue_id": "loader-btcusdt-dummy-2024-06-01-testid",
  "ping_ts": 1754202651.997,
  "ponged_at": 1754202652.045
}
```

---

## 6. Additional Notes

* RTT is calculated as `ponged_at - ping_ts`.
* Can be used in CI/CD pipelines for Kafka connectivity tests.
* Built-in Kafka consumer automatically disconnects after receiving `pong`.

---

## 7. Recommendations

* Run inside the Kubernetes cluster as a `Job` for diagnostics.
* Integrate into GitLab CI to verify Kafka and queue availability.
* Suitable for monitoring `queue-events` and testing loader/connector microservices.

