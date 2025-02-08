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