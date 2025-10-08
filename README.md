# MediaWiki Kafka Ingester

This application ingests MediaWiki event streams and sends them to Kafka topics.

## Features

- **Page Create Events**: Ingests `mediawiki.page-create` events from Wikimedia's event stream
- **Page Delete Events**: Ingests `mediawiki.page-delete` events from Wikimedia's event stream
- **Kafka Integration**: Sends events to Kafka topics with proper configuration
- **Graceful Shutdown**: Handles SIGINT and SIGTERM signals for clean shutdown

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka.kafka:9092` | Kafka bootstrap servers |
| `KAFKA_TOPIC` | `mediawiki.page-create` | Kafka topic for page-create events |
| `EVENTSTREAM_URL` | `https://stream.wikimedia.org/v2/stream/mediawiki.page-create` | MediaWiki event stream URL |

For page-delete events, the following environment variables are used:
- `KAFKA_TOPIC` defaults to `mediawiki.page-delete`
- `EVENTSTREAM_URL` defaults to `https://stream.wikimedia.org/v2/stream/mediawiki.page-delete`

## Applications

### 1. Page Create Ingester (`src/page_create_app.py`)
- Ingests MediaWiki page creation events
- Sends to `mediawiki.page-create` Kafka topic
- User-Agent: `k8s-data-platform-mediawiki-kafka-ingester`

### 2. Page Delete Ingester (`src/page_delete_app.py`)
- Ingests MediaWiki page deletion events
- Sends to `mediawiki.page-delete` Kafka topic
- User-Agent: `k8s-data-platform-mediawiki-kafka-ingester-page-delete`

### 3. Common Module (`src/common.py`)
- Shared functions for both applications
- Kafka configuration and producer setup
- Event stream processing logic
- Signal handling for graceful shutdown

## Docker

The Dockerfile runs both applications simultaneously using a startup script that:
1. Starts the page-create ingester in the background
2. Starts the page-delete ingester in the background
3. Waits for both processes to complete

## Kafka Configuration

The application uses the following Kafka producer configuration:
- **Acknowledgment**: `all` (wait for all replicas)
- **Idempotence**: Enabled
- **Compression**: ZSTD
- **Security**: SASL_PLAINTEXT with PLAIN mechanism
- **Linger**: 50ms
- **Max in-flight requests**: 5
- **Delivery timeout**: 120 seconds

## Usage

### Local Development

```bash
# Install dependencies
uv sync

# Run page-create ingester
python src/page_create_app.py

# Run page-delete ingester
python src/page_delete_app.py
```

### Docker

```bash
# Build image
docker build -t mediawiki-kafka-ingester .

# Run container
docker run -e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 mediawiki-kafka-ingester
```

### Kubernetes

The application can be deployed to Kubernetes with appropriate environment variables and Kafka configuration.

```bash
# Deploy page-create ingester
kubectl apply -f k8s/page-create-deployment.yaml

# Deploy page-delete ingester
kubectl apply -f k8s/page-delete-deployment.yaml
```
