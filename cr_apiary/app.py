import base64, os, time
from flask import Flask, request
from opencensus.ext.stackdriver import trace_exporter as stackdriver_exporter
import opencensus.trace.tracer

from google.cloud import logging
from googleapiclient.discovery import build


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
log_name = "cr_apiary"
logger = logging_client.logger(log_name)


# Build the Apiary client.
topic_path = 'projects/{}/topics/{}'.format(
    PROJECT_ID,
    'apiary',
)
service = build('pubsub', 'v1')


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        n = int(request.get_json().get("n"))
    else:
        n = 10

    tracer = initialize_tracer(PROJECT_ID)

    with tracer.span(name="cr_apiary") as span:
        latencies = []
        message = base64.b64encode(b'first')
        body = {'messages': [{'data': message.decode('utf-8')}]}
        temp = time.time()
        response = service.projects().topics().publish(
            topic=topic_path,
            body=body,
        ).execute()
        assert response['messageIds']
        logger.log_text(f"{int((time.time()- temp)*1000)}")

        for i in range(n):
            message = base64.b64encode(str(i).encode('utf-8'))
            body = {'messages': [{'data': message.decode('utf-8')}]}
            temp = time.time()
            response = service.projects().topics().publish(
                topic=topic_path,
                body=body,
            ).execute()
            assert response['messageIds']
            latencies.append(time.time() - temp)

    logger.log_text(f"{','.join([str(int(i*1000)) for i in latencies])}")
    return("Published messages.\n")


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
