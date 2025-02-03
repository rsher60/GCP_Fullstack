# Assign Service account user role to the service account


# Use your project ID and for the service account you have to use project number. You can get your
#project number from the overview section of the cloud console UI.
gcloud projects add-iam-policy-binding copper-index-447603-b3 \
--member=serviceAccount:1031406148701@cloudbuild.gserviceaccount.com --role=roles/iam.serviceAccountUser


# Assign Cloud Run role to the service account
gcloud projects add-iam-policy-binding copper-index-447603-b3 \
  --member=serviceAccount:1031406148701@cloudbuild.gserviceaccount.com --role=roles/run.admin



#Command to trigger a build
#Take extra care to make sure the artifacts are in the same region
gcloud builds submit --region us-central1
