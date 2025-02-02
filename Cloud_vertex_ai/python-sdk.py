from google.cloud import aiplatform


project_id = "copper-index-447603-b3"
region = "us-central1"
staging_bucket="gs://prediction-bucket-rsher60"

aiplatform.init(project=project_id, location=region, staging_bucket=staging_bucket)

job = aiplatform.CustomTrainingJob(
        display_name="credit-score-training-job",
        script_path="model-training-code.py",
        container_uri="us-docker.pkg.dev/vertex-ai/training/sklearn-cpu.1-0:latest",
        requirements=["gcsfs"]
    )

job.run(
    replica_count=1,
    machine_type="n1-standard-4",
    sync=True
)
job.wait()


display_name = "credit-card-prediction-model-sdk"
artifact_uri = "gs://rsher60-training-bucket/credit-card-training/"
serving_container_image_uri = "us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.1-5:latest"

model = aiplatform.Model.upload(
        display_name=display_name,
        artifact_uri=artifact_uri,
        serving_container_image_uri=serving_container_image_uri,
        sync=False
    )

deployed_model_display_name = "credit-card-prediction-endpoint"
traffic_split = {"0": 100}
machine_type = "n1-standard-4"
min_replica_count = 1
max_replica_count = 1

endpoint = model.deploy(
        deployed_model_display_name=deployed_model_display_name,
        traffic_split=traffic_split,
        machine_type=machine_type,
        min_replica_count=min_replica_count,
        max_replica_count=max_replica_count
    )


#Once the endpoint is reated you can get the endpoint ID from the UI and other details

"""Function to test the online prediction """

def endpoint_predict_sample(
    project: str, location: str, instances: list, endpoint: str
):
    aiplatform.init(project=project, location=location)

    endpoint = aiplatform.Endpoint(endpoint)

    prediction = endpoint.predict(instances=instances)
    #print(prediction)
    return prediction

#NOTE: instances should be preporcessed and label encoded, one hot encoded in the same format as the
# the training dataframe X was.

#You also need to take care that you might have unseen labels in the new dataset during online prediction.

instances = [[23.0,
 12.0,
 19114.12,
 3.0,
 4.0,
 3.0,
 4.0,
 6.0,
 11.27,
 4.0,
 1.0,
 809.98,
 24.797346908844982,
 186.0,
 1.0,
 49.57494921489417,
 1.0,
 341.48923103222177],[23.0,
 12.0,
 19114.12,
 3.0,
 4.0,
 34.0,
 4.0,
 64.0,
 11.27,
 4.0,
 1.0,
 809.98,
 24.797346908844982,
 186.0,
 1.0,
 49.57494921489417,
 1.0,
 341.48923103222177]]