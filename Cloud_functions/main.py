import pandas as pd
import requests
import vertexai
from io import BytesIO
from vertexai.generative_models import Part, Image, GenerativeModel
import weaviate
import warnings
warnings.filterwarnings("ignore")
import weaviate.classes as wvc
import openai
import functions_framework

import vertexai
from io import BytesIO
from vertexai.generative_models import Part, GenerativeModel
from google.cloud import storage

"""
image_path = "https://i.natgeofe.com/n/548467d8-c5f1-4551-9f58-6817a8d2c45e/NationalGeographic_2572187_square.jpg" # this link is an example
response = requests.get(image_path)
im_bytes = BytesIO(response.content)
image_part = Part.from_data(
    im_bytes.getvalue(),
    mime_type='image/jpeg'
)

vertexai.init(project="copper-index-447603-b3", location="us-central1") # Don't forget to set these
model = GenerativeModel(model_name="gemini-1.0-pro-vision-001")

query = "Please describe the image."
response = model.generate_content(
    [image_part, query]
)

"""



# Replace with your project ID, bucket name, and blob name (image file name).
project_id = "copper-index-447603-b3"  # your-project-id
bucket_name = "ai-image-cloudfn"  # your-gcs-bucket-name
blob_name = "CamScanner Answer.jpg"  # path/to/image/in/bucket.jpg

vertexai.init(project=project_id, location="us-east1")
model = GenerativeModel(model_name="gemini-1.0-pro-vision-001")

# Initialize a GCS client
storage_client = storage.Client(project=project_id)


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)
    blob_list = []
    # Note: The call returns a response only when the iterator is consumed.
    for blob in blobs:
        #print(blob.name)
        blob_list.append(blob.name)
    return blob_list


@functions_framework.cloud_event
def summarise_image(cloud_event):
    file_name = []
    image_summary = []
    for i in list_blobs(bucket_name):

        try:
            # Get the bucket
            bucket = storage_client.bucket(bucket_name)
            # Get the blob (image file)
            blob = bucket.blob(i)
            # Download the image data as bytes
            im_bytes = BytesIO(blob.download_as_bytes())
            file_name.append(i)

            image_part = Part.from_data(
                im_bytes.getvalue(),
                mime_type='image/png'  # Adjust mime_type if necessary (e.g., 'image/png')
            )

            query = "Generate a detailed summary of this image for a blind person"
            response = model.generate_content(
                [image_part, query]
            )

            for candidate in response.candidates:
                #print(f"Response: {candidate.text}")
                image_summary.append(candidate.text)


        except Exception as e:
            print(f"Error: {e}")


    df = pd.DataFrame()
    df['file_names'] = file_name
    df['image_summary'] = image_summary


    if len(df['file_names']) == len(df['image_summary']):
        print(df['image_summary'])



    # Weaviate Entrypoint

    weaviate_url = "https://r4hyygvpruakgmjjvuktgq.c0.us-east1.gcp.weaviate.cloud"
    weaviate_api_key = "yh3c2c2PV24m8OcjEcmK4zUgnbM0YHxHJiXi"
    openai.api_key ="sk-proj-bNSscy3CEhnZuHXwmtkTT3BlbkFJTaCScwqrSKH0g8P6ALwW"
    headers = {
        "X-OpenAI-Api-Key": openai.api_key,
    }



    with weaviate.connect_to_wcs(
        cluster_url=weaviate_url,  # Replace with your Weaviate Cloud URL
        auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),  # Replace with your Weaviate Cloud key
        headers=headers,
        skip_init_checks=True
    ) as client:  # Use this context manager to ensure the connection is closed
        print(client.is_ready())

    client.connect()

    client.collections.delete("Image_summaries_gcloud_functions")
    image_summaries = client.collections.create(
            "Image_summaries_gcloud_functions",
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),
            properties=[
            wvc.config.Property(
                name="file_names",
                data_type=wvc.config.DataType.TEXT,
                vectorize_property_name=False
            ),
            wvc.config.Property(
                name="image_summary",
                data_type=wvc.config.DataType.TEXT,
                vectorize_property_name=False
            ),

        ],
        # Configure the vector index
        vector_index_config=wvc.config.Configure.VectorIndex.hnsw(  # Or `flat` or `dynamic`
            distance_metric=wvc.config.VectorDistances.COSINE,
            quantizer=wvc.config.Configure.VectorIndex.Quantizer.bq(),
        ),
    )

    #Ensure all the columns are string and fillna

    knowledge_base = []
    for idx, row in df.iterrows():
        knowledge_base.append({
            'file_names': str(row['file_names']),
            'image_summary': str(row['image_summary']),
        })


#This will be part of the script that uses the LLM. You need to make the connection with the gemini

    classs = client.collections.get("Image_summaries_gcloud_functions")
    with classs.batch.dynamic() as batch:
        for i in knowledge_base[:5000]:
            batch.add_object(
                properties=i
            )

    aggregation = image_summaries.aggregate.over_all(total_count=True)
    print(aggregation.total_count)

    #Query the collection
    response = classs.query.bm25(
        query="sample question paperz",
        limit=3
    )

    for o in response.objects:
        print(o.properties)