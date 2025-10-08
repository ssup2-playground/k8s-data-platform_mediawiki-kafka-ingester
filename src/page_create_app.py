import os
import asyncio
from common import run_event_stream_processor

# Environment variables
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "mediawiki.page-create")
EVENTSTREAM_URL = os.getenv("EVENTSTREAM_URL", "https://stream.wikimedia.org/v2/stream/mediawiki.page-create")
USER_AGENT = "k8s-data-platform-mediawiki-kafka-ingester"

async def main():
    """Main function for page-create event processing"""
    await run_event_stream_processor(KAFKA_TOPIC, EVENTSTREAM_URL, USER_AGENT)

# Entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")