# Setup for Publish Latency Testing

Each directory in this repo contains the necessary files for deploying a simple app that publishes some messages using [Google Cloud Pub/Sub] in a serverless app.  

|__Directory__|__Description__|
|---|---| 
|`cf_apiary`|A [Cloud Function] that publishes messages using the Cloud Pub/Sub Apiary client.| 
|`cf_cl_mixed`|A [Cloud Function] that publishes messages using the Cloud Pub/Sub standard client. The first [publish future] is resolved in a callback function. The subsequent publish futures are resolved sequentially.|
|`cf_gapic`|A [Cloud Function] that publishes messages using the Cloud Pub/Sub GAPIC client.|
|`cr_apiary`|A [Cloud Run] app that publishes messages using the Cloud Pub/Sub Apiary client.|
|`cr_cl_mixed`|A [Cloud Run] app that publishes messages using the Cloud Pub/Sub standard client. The first [publish future] is resolved in a callback function. The subsequent publish futures are resolved sequentially.|
|`cr_gapic`|A [Cloud Run] app that publishes messages using the Cloud Pub/Sub GAPIC client.|
|`gae_apiary`|An [App Engine] app that publishes messages using the Cloud Pub/Sub Apiary client.|
|`gae_cl_mixed`|An [App Engine] app that publishes messages using the Cloud Pub/Sub standard client. The first [publish future] is resolved in a callback function. The subsequent publish futures are resolved sequentially.|
|`gae_gapic`|An [App Engine] app that publishes messages using the Cloud Pub/Sub GAPIC client.|


## Before you begin

1. Install the [Cloud SDK].

1. [Create a new project].

1. [Enable billing].

1. [Enable the APIs](https://console.cloud.google.com/flows/enableapi?apiid=logging,pubsub,appengine,cloudbuild,run,cloudtrace,cloudfunctions): Stackdriver Logging, Stackdriver Trace, Cloud Pub/Sub, App Engine, Cloud Run, Cloud Functions, Cloud Build.

1. Setup the Cloud SDK to your GCP project.

   ```bash
   gcloud init
   ```

1. [Create a service account key] as a JSON file.
   For more information, see [Creating and managing service accounts].

   * From the **Service account** list, select **New service account**.
   * In the **Service account name** field, enter a name.
   * From the **Role** list, select **Project > Owner**.

     > **Note**: The **Role** field authorizes your service account to access resources.
     > You can view and change this field later by using the [GCP Console IAM page].
     > If you are developing a production app, specify more granular permissions than **Project > Owner**.
     > For more information, see [Granting roles to service accounts].

   * Click **Create**. A JSON file that contains your key downloads to your computer.

1. Set your `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account key file.

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
   ```

1. Create some Pub/Sub topics for testing the three different types of publish clients.
    ```bash
    gcloud pubsub topics create apiary
    glcoud pubsub topics create standard
    gcloud pubsub topics create gapic
    ```


## Setup

### Cloud Function

1. Open `cf.*.py` and update `PROJECT_ID` with your project ID.

1. Deploy the function.

    ```bash
    gcloud functions deploy [your_function_name] \
      --runtime python37 \
      --trigger-http
    ```

1. Test publish latency.

    ```bash
    curl -X POST "https://us-central1-[your-project-id].cloudfunctions.net/[your-function-name]" \
      -H "Content-Type:application/json" \
      --data '{"n":"100"}'
    ```

### Google App Engine

1. Deploy the app.

    ```bash
    gcloud app deploy --version [your-version-name]
    ```

1. Test publish latency.

    ```bash
    curl -X POST "https://[your-version-name]-dot-[your-project-id].appspot.com/" \
      -H "Content-Type:application/json" \
      --data '{"n":"100"}'
    ```

### Cloud Run

1. Open `Dockerfile` and update `your-project-id` with your project ID.

1. Build your container image.

    ```bash
    gcloud builds submit --tag gcr.io/[your-project-id]/[your-image-name]
    ```

1. Deploy to Cloud Run and record the Service URL returned.

    ```bash
    gcloud beta run deploy \
      --image gcr.io/[your-project-id]/[your-image-name] \
      --platform managed
    ```
    
1. Test publish latency.

    ```bash
    curl -X POST "https://[your-image-name]-[your-hash-from-the-service-url].a.run.app/" \
      -H "Content-Type:application/json" \
      --data '{"n": "100"}'
    ```

To run the cURL commands repeatedly and record the end-to-end latencies, try:

```bash
for i in `seq 1 10`; do $your-curl-command -o /dev/null -w %{time_total}\\n >> output.txt; done;
```

To run the cURL commands in a parallel fashion, create a `postfile` that specifies the value that `n` should take, then use Apache Benchmark and do something like: 

```bash
ab -n 10 -c 2 -s 1800 -T 'application/json' -p postfile [your-endpoint]
```


## Getting latency data

1. One way to see latency data is in the GCP [Stackdriver Trace] page. 

1. The other way to latency data is in the GCP [Stackdriver Logging] page. Here, you will need to navigate to the appropriate logs. You can download the logs locally and parse the data for analysis.

[Cloud Function]: https://cloud.google.com/functions/docs/
[Google Cloud Pub/Sub]: https://cloud.google.com/pubsub/docs/
[publish future]: https://googleapis.github.io/google-cloud-python/latest/pubsub/publisher/api/futures.html
[publish futures]: https://googleapis.github
[App Engine]: https://cloud.google.com/appengine/docs/
[Cloud Run]: https://cloud.google.com/run/docs/

[Cloud SDK]: https://cloud.google.com/sdk/docs/
[Create a new project]: https://console.cloud.google.com/projectcreate
[Enable billing]: https://cloud.google.com/billing/docs/how-to/modify-project
[Create a service account key]: https://console.cloud.google.com/apis/credentials/serviceaccountkey
[Creating and managing service accounts]: https://cloud.google.com/iam/docs/creating-managing-service-accounts
[GCP Console IAM page]: https://console.cloud.google.com/iam-admin/iam
[Granting roles to service accounts]: https://cloud.google.com/iam/docs/granting-roles-to-service-accounts

[Stackdriver Trace]: https://console.cloud.google.com/traces
[Stackdriver Logging]: https://console.cloud.google.com/logs
