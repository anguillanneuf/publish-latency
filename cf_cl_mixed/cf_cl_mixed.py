import json, os, time
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer

from google.cloud import logging, pubsub_v1


PROJECT_ID = 'your-project_id'  # TODO: Use your project ID.


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
log_name = "cf_cl_mixed"
logger = logging_client.logger(log_name)


# Initialize the standard publisher client.
batch_settings = pubsub_v1.types.BatchSettings(max_messages = 1)
client = pubsub_v1.PublisherClient(batch_settings)
topic_path = client.topic_path(PROJECT_ID, "standard")


def hello_world(request):
    request_json = request.get_json(silent=True)

    if 'n' in request_json:
        n = int(request_json['n'])
    else:
        n = 10

    tracer = initialize_tracer(PROJECT_ID)

    def get_callback(f, data):
        def callback(f):
            try:
                f.result()
                logger.log_text(f"{int((time.time()- futures[data])*1000)}")
            except Exception:
                raise Exception
        return callback

    with tracer.span(name="cf_cl_mixed") as span:
        futures = dict()
        latencies = []

        futures.update({b"first": time.time()})
        future = client.publish(topic_path, data=b"first")
        future.add_done_callback(get_callback(future, b"first"))

        for i in range(n):
            data = str(i)
            temp = time.time()
            future = client.publish(topic_path, data=data.encode('utf-8'))
            future.result()
            latencies.append(time.time() - temp)

    logger.log_text(f"{','.join([str(int(i*1000)) for i in latencies])}")
    return("Published messages.")
