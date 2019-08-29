import os
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer
import time

from google.cloud import logging
from google.cloud.pubsub_v1.gapic import publisher_client


PROJECT_ID = 'your-project-id'  # TODO: Use your project ID.


def initialize_tracer(project_id):
    exporter = stackdriver_exporter.StackdriverExporter(
        project_id=project_id
    )
    tracer = opencensus.trace.tracer.Tracer(
        exporter=exporter,
        sampler=opencensus.trace.tracer.samplers.AlwaysOnSampler()
    )
    return tracer


logging_client = logging.Client()
log_name = "cf_gapic"
logger = logging_client.logger(log_name)


# Initialize the GAPIC client.
client = publisher_client.PublisherClient()
topic_path = client.topic_path(PROJECT_ID, "gapic")


def hello_world(request):
    request_json = request.get_json(silent=True)

    if 'n' in request_json:
        n = int(request_json['n'])
    else:
        n = 10

    tracer = initialize_tracer(PROJECT_ID)

    with tracer.span(name="cf_gapic") as span:
        latencies = []

        temp = time.time()
        response = client.publish(topic_path, [{'data': b'first'}])
        assert response.message_ids
        logger.log_text(f"{int((time.time()- temp)*1000)}")

        for i in range(n):
            messages = [{'data': str(i).encode('utf-8')}]
            temp = time.time()
            response = client.publish(topic_path, messages)
            assert response.message_ids
            latencies.append(time.time() - temp)

    logger.log_text(f"{','.join([str(int(i*1000)) for i in latencies])}")
    return("Published messages.")
