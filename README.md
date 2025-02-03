
# GCP_Fullstack



## For the Python Training:

You should see a model.joblib and label_encoder file which should be used on the new data.










## Shell commands to Create a docker image and deploy it as a Cloud run service

1) ``` docker build -t ml-flask-app .```
2) ``` docker tag ml-flask-app gcr.io/copper-index-447603-b3/ml-flask-app ```
3) ``` docker push gcr.io/copper-index-447603-b3/ml-flask-app ```
4) ``` docker run deploy ml-flask-app --image gcr.io/copper-index-447603-b3/ml-flask-app ```


These commands will create a docker image that can be deployed from CLoud Run UI or using the command 

``` gcloud run deploy demo-flask-app --image gcr.io/udemy-mlops-395416/demo-flask-app --region us-central1```


##For Cloudbuild:

1) you need to create a repository in advance.

## TODO 

### Sun Feb 2, 2025 : 
1) Modifiy and add the code to do preprocessing and label encoding on the app side
2) Add the code for UI in the fastapi 
3) Work on the CI/CD aspect with cloud build

