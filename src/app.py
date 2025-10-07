import os, json, signal, asyncio, uuid
import aiohttp
from confluent_kafka import Producer

# Environment variables
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka.kafka:9092")
KAFKA_TOPIC             = os.getenv("KAFKA_TOPIC", "mediawiki.page-create")
EVENTSTREAM_URL         = os.getenv("EVENTSTREAM_URL", "https://stream.wikimedia.org/v2/stream/mediawiki.page-create")

# Function
def get_kafka_config():
    """Get Kafka configuration"""
    return {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "acks": "all",
        "enable.idempotence": True,
        "compression.type": "zstd",

        "security.protocol": "SASL_PLAINTEXT",
        "sasl.mechanisms": "PLAIN",
        "sasl.username": "user",
        "sasl.password": "user",

        "linger.ms": 50,
        "max.in.flight.requests.per.connection": 5,
        "delivery.timeout.ms": 120000,
    }

def setup_signal_handlers(shutdown_event):
    """Setup signal handlers for graceful shutdown"""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: shutdown_event.set())
        except NotImplementedError:
            signal.signal(sig, lambda *_: shutdown_event.set())

async def process_event(producer, event_data):
    """Send event to Kafka"""
    try:
        producer.produce(
            topic=KAFKA_TOPIC,
            key=uuid.uuid4().bytes,
            value=json.dumps(event_data, ensure_ascii=False).encode("utf-8"),
        )
        producer.poll(0)
    except Exception as e:
        print(f"Failed to produce event: {e}")

async def process_stream_line(line, buf):
    """Process stream line and update buffer"""
    if line.startswith("data:"):
        buf.append(line[5:].lstrip())
    return buf

async def main():
    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)
    
    producer = Producer(get_kafka_config())
    
    async with aiohttp.ClientSession() as session:
        while not shutdown_event.is_set():
            try:
                headers = {
                    "Accept": "text/event-stream",
                    "User-Agent": "k8s-data-platform-mediawiki-kafka-ingester"
                }
                async with session.get(EVENTSTREAM_URL, headers=headers) as response:
                    response.raise_for_status()
                    buf = []
                    
                    async for raw in response.content:
                        if shutdown_event.is_set():
                            break
                            
                        line = raw.decode("utf-8", "ignore").rstrip("\n")
                        
                        if not line and buf:
                            try:
                                event = json.loads("\n".join(buf))
                                await process_event(producer, event)
                            except json.JSONDecodeError:
                                print("Failed to parse JSON event")
                            buf.clear()
                            continue
                            
                        buf = await process_stream_line(line, buf)
                        
            except aiohttp.ClientError as e:
                print(f"HTTP error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Unexpected error: {e}")
                await asyncio.sleep(5)

    producer.flush(10)

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")