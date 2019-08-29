from flask import Flask, request
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer
import os, time

from google.cloud import logging
from google.cloud.pubsub_v1.gapic import publisher_client


PROJECT_ID = os.environ("GOOGLE_CLOUD_PROJECT")


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
log_name = "gae_gapic"
logger = logging_client.logger(log_name)


# Initialize the GAPIC client.
client = publisher_client.PublisherClient()
topic_path = client.topic_path(PROJECT_ID, "gapic")


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        n = int(request.get_json().get("n"))
    else:
        n = 10

    tracer = initialize_tracer(PROJECT_ID)

    with tracer.span(name="gae_gapic") as span:
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
    return("Published messages.\n")


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
