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
from cloudevents.http import CloudEvent
import vertexai
from io import BytesIO
from vertexai.generative_models import Part, GenerativeModel
from google.cloud import storage

from google.cloud import secretmanager

# Access secrets from Google Secret Manager
client = secretmanager.SecretManagerServiceClient()


def access_secret(secret_id):
    """Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    return payload


# Replace with your project ID, bucket name, and blob name (image file name).
project_id = "copper-index-447603-b3"  # your-project-id
bucket_name = "ai-image-cloudfn"  # your-gcs-bucket-name
blob_name = "CamScanner Answer.jpg"  # path/to/image/in/bucket.jpg

vertexai.init(project=project_id, location="us-east1")
model = GenerativeModel(model_name="gemini-1.0-pro-vision-001")

# Initialize a GCS client
storage_client = storage.Client(project=project_id)

weaviate_url_secret_id = "weaviate_url"
weaviate_api_key_secret_id = "weaviate_api_key"
openai_api_key_secret_id = "openai_api_key"


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)
    blob_list = []
    # Note: The call returns a response only when the iterator is consumed.
    for blob in blobs:
        # print(blob.name)
        blob_list.append(blob.name)
    return blob_list


@functions_framework.cloud_event
def process_and_upload_image_summaries(cloud_event: CloudEvent):
    """
    Summarizes images from a GCS bucket, uploads the summaries to Weaviate, and returns the total count.

    Args:
        bucket_name: The name of the GCS bucket containing the images.
        weaviate_url_secret_id: Secret ID for the Weaviate URL.
        weaviate_api_key_secret_id: Secret ID for the Weaviate API key.
        openai_api_key_secret_id: Secret ID for the OpenAI API key.
        access_secret: Callable function to retrieve secrets.

    Returns:
        The total count of uploaded image summaries.
    """

    file_names = []
    image_summaries = []
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    bucket_name = data["bucket"]

    for blob_name in list_blobs(bucket_name):  # Directly iterate over blob names
        try:
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            image_bytes = BytesIO(blob.download_as_bytes())
            file_names.append(blob_name)

            image_part = Part.from_data(
                image_bytes.getvalue(),
                mime_type='image/png'
            )

            response = model.generate_content(
                [image_part, "Generate a detailed summary of this image for a blind person"]
            )

            image_summaries.append(response.candidates[0].text)  # Take the first candidate

        except Exception as e:
            print(f"Error processing {blob_name}: {e}")  # More informative error message
            # Consider adding more robust error handling, e.g., retrying or logging

    df = pd.DataFrame({'file_names': file_names, 'image_summary': image_summaries})

    # Access secrets only once, after processing all images and before Weaviate interaction

    weaviate_url = access_secret(weaviate_url_secret_id)
    weaviate_api_key = access_secret(weaviate_api_key_secret_id)
    openai.api_key = access_secret(openai_api_key_secret_id)  # Assuming openai is imported
    
    

    headers = {"X-OpenAI-Api-Key": openai.api_key}

    try:
        with weaviate.connect_to_wcs(
                cluster_url=weaviate_url,
                auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
                headers=headers,
                skip_init_checks=True  # Remove this for initial testing
        ) as client:
            # No need to call client.connect() explicitly within the 'with' block
            print("Weaviate connection successful:", client.is_ready())

            client.collections.delete(
                "Image_summaries_gcloud_functions")  # Consider a different collection name each time? Avoids accumulation
            image_summaries_collection = client.collections.create(  # More descriptive variable name
                "Image_summaries_gcloud_functions",  # Consider a more descriptive or parameterized collection name
                vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_openai(),
                properties=[
                    wvc.config.Property(name="file_names", data_type=wvc.config.DataType.TEXT,
                                        vectorize_property_name=False),
                    wvc.config.Property(name="image_summary", data_type=wvc.config.DataType.TEXT,
                                        vectorize_property_name=False),
                ],
                vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                    distance_metric=wvc.config.VectorDistances.COSINE,
                    quantizer=wvc.config.Configure.VectorIndex.Quantizer.bq(),
                ),
            )

            with image_summaries_collection.batch.dynamic() as batch:  # Use the collection variable
                for _, row in df.iterrows():
                    batch.add_object(properties={
                        'file_names': str(row['file_names']),  # str() conversion already handled in DataFrame creation
                        'image_summary': str(row['image_summary']),
                    })

            aggregation = image_summaries_collection.aggregate.over_all(total_count=True)  # Use the collection variable
            return aggregation.total_count

    except Exception as e:
        print(f"Error interacting with Weaviate: {e}")
        return 0  # or raise the exception depending on your needs


