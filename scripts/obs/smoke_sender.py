"""Send a guaranteed trace span via OTLP -> collector.

Requires: pip install -e '.[otel]'
"""
import os
import time

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def main() -> int:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    service_name = os.getenv("OTEL_SERVICE_NAME", "peak_trade_smoke_sender")

    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("peak_trade.obs.smoke")

    with tracer.start_as_current_span("p2_3_smoke_span") as span:
        span.set_attribute("smoke", True)
        span.set_attribute("ts", time.time())
        time.sleep(0.05)

    # flush
    provider.shutdown()
    print(f"✅ Sent span to {endpoint} (service={service_name})")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
