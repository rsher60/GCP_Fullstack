# APIs to be enabled
- cloud function
- cloud build
- eventarc
- cloud run admin api
- artifact registry

PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects list --filter="project_id:$PROJECT_ID" --format='value(project_number)')
SERVICE_ACCOUNT=$(gsutil kms serviceaccount -p $PROJECT_NUMBER)

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:$SERVICE_ACCOUNT \
  --role roles/pubsub.publisher

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member serviceAccount:$SERVICE_ACCOUNT \
  --role roles/run.admin


gcloud functions deploy summarise_image \
--gen2 \
--runtime=python311 \
--region=us-east1 \
--source=. \
--entry-point=summarise_image \
--trigger-event-filters="type=google.cloud.storage.object.v1.finalized" \
--trigger-event-filters="bucket=ai-image-cloudfn"
--memory=4GB
--cpu=2
# --max-instances



#gsutil cp us-states.csv gs://cloud-func-trigger/us-states.csv

#gcloud beta functions logs read python-load-bq --gen2 --limit=100


## Deploy commands for the hello world project


gcloud beta run deploy llm-summary \
      --source . \
      --function process_and_upload_image_summaries \
      --base-image python312 \
      --region us-east1 \
      --memory 2G





gcloud eventarc triggers create llm-summary-trigger \
    --location=us-east1 \
    --destination-run-service=llm-summary \
    --destination-run-region=us-east1 \
    --event-filters="type=google.cloud.storage.object.v1.finalized" \
    --event-filters="bucket=ai-image-cloudfn" \
    --service-account=1031406148701-compute@developer.gserviceaccount.com



gcloud eventarc triggers list --location=us-east1

 echo "Hello World" > random.txt
 gcloud storage cp random.txt gs://ai-image-cloudfn/random.txt

# deploy commands testing



gcloud beta run deploy llm-summary1 \
      --source . \
      --function process_and_upload_image_summaries \
      --base-image python312 \
      --region us-east1 \
      --memory 2G





gcloud eventarc triggers create llm-summary-trigger1 \
    --location=us-east1 \
    --destination-run-service=llm-summary1 \
    --destination-run-region=us-east1 \
    --event-filters="type=google.cloud.storage.object.v1.finalized" \
    --event-filters="bucket=ai-image-cloudfn" \
    --service-account=1031406148701-compute@developer.gserviceaccount.com