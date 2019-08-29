from flask import Flask, request
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer
import os, time

from google.cloud import pubsub_v1, logging


PROJECT_ID = os.environ('GOOGLE_CLOUD_PROJECT')


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
log_name = "gae_cl_mixed"
logger = logging_client.logger(log_name)


# Initialize the standard publisher client.
batch_settings = pubsub_v1.types.BatchSettings(max_messages = 1)
client = pubsub_v1.PublisherClient(batch_settings)
topic_path = client.topic_path(PROJECT_ID, "standard")


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        n = int(request.get_json().get("n"))
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

    with tracer.span(name="gae_cl_mixed") as span:
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
    return("Published messages.\n")

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
