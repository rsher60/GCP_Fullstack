import time
import pandas as pd
import requests
import vertexai
import requests
from requests import exceptions
from io import BytesIO
from vertexai.generative_models import Part, Image, GenerativeModel
import weaviate
import warnings
import logging
warnings.filterwarnings("ignore")
import weaviate.classes as wvc
import openai
import functions_framework
from cloudevents.http import CloudEvent
import vertexai
from io import BytesIO
from vertexai.generative_models import Part, GenerativeModel
from google.cloud import storage
from requests import exceptions
from google.cloud import secretmanager

# Access secrets from Google Secret Manager
client = secretmanager.SecretManagerServiceClient()
# Replace with your project ID, bucket name, and blob name (image file name).
project_id = "copper-index-447603-b3"  # your-project-id

def access_secret(secret_id):
    """Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"  # Correct way to format secret name

    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    return payload


# Replace with your project ID, bucket name, and blob name (image file name).
project_id = ""  # your-project-id
bucket_name = ""  # your-gcs-bucket-name
blob_name = ""  # path/to/image/in/bucket.jpg

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
def main(cloud_event: CloudEvent):
#def main():
    """
    Summarizes images from a GCS bucket, uploads the summaries to Weaviate, and returns the total count.

    Args:
      cloud_event: The CloudEvent that triggered the function.

    Returns:
      A string indicating completion.  The aggregation count is logged.
    """
    max_retries = 5
    retry_delay = 1  # Initial delay in seconds

    file_names = []
    image_summaries = []
    data = cloud_event.data

    event_id = cloud_event["id"]
    event_type = cloud_event["type"]

    bucket_name = data["bucket"]
    #bucket_name="ai-image-cloudfn"

    total_uploaded = 0
    for blob_name in list_blobs(bucket_name):  # Directly iterate over blob names
        retries = 0

        while retries < max_retries:  # Corrected loop condition
            try:
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                image_bytes = BytesIO(blob.download_as_bytes())

                logging.info(f"Processing image: {blob_name}")
                print(f"Processing image: {blob_name}")
                image_part = Part.from_data(
                    image_bytes.getvalue(), mime_type="image/jpeg"  # Assuming JPEG, adjust if necessary
                )

                response = model.generate_content(
                    [image_part, "Generate a detailed summary of this image for a blind person"]
                )

                if response.candidates and response.candidates[0].content.parts:
                    summary = response.candidates[0].content.parts[0].text  # Access text correctly
                    image_summaries.append(summary)
                    file_names.append(blob_name)
                    total_uploaded += 1
                    logging.info(f"Image summary generated for {blob_name} with {len(summary)} tokens")
                    break  # Successful, exit retry loop
                else:
                    logging.warning(f"No text in the response for {blob_name}. Response: {response}")
                    print(f"No text in the response for {blob_name}. Response: {response}")
                    image_summaries.append("No summary available")
                    file_names.append(blob_name)
                    break  # exit retry loop

            except Exception as e:
                if "429" in str(e):  # Check if it's a 429 error
                    logging.warning(f"Received 429 error for {blob_name}. Retry {retries + 1}/{max_retries}. Error: {e}")
                    retries += 1
                    time.sleep(retry_delay)  # Wait before retrying
                    retry_delay *= 2  # Exponential backoff
                else:
                    logging.error(f"Error processing {blob_name}: {e}")
                    image_summaries.append(f"Error: {e}")  # Or some other error message
                    file_names.append(blob_name)
                    break  # Exit retry loop for non-429 errors

        else:
            logging.error(f"Failed to process {blob_name} after {max_retries} retries due to 429 errors.")
            image_summaries.append("Failed to generate summary due to quota errors.")
            file_names.append(blob_name)

    df = pd.DataFrame({"file_names": file_names, "image_summary": image_summaries})
    df.drop_duplicates(subset='file_names', keep="last")
    logging.info(f"Dataframe is generated with {df.shape}")
    print(f"dataframe is generated with {df.shape}")


    headers = {"X-OpenAI-Api-Key": openai.api_key}
    # Access secrets only once, after processing all images and before Weaviate interaction
    weaviate_url = access_secret(weaviate_url_secret_id)
    weaviate_api_key = access_secret(weaviate_api_key_secret_id)
    # Assuming openai is imported, and openai.api_key is used later in Weaviate upload process
    openai.api_key = access_secret(openai_api_key_secret_id)


    try:
        with weaviate.connect_to_wcs(
            cluster_url=weaviate_url,
            auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
            headers=headers,
            skip_init_checks=True  # Remove this for initial testing
        ) as client:
            # No need to call client.connect() explicitly within the 'with' block
            print("Weaviate connection successful:", client.is_ready())

            try:
              client.collections.delete(
                  "Image_summaries_gcloud_functions")  # Consider a different collection name each time? Avoids accumulation
            except weaviate.exceptions.UnexpectedStatusCodeException as e:
              logging.warning(f"Collection 'Image_summaries_gcloud_functions' might not exist, or deletion failed.  Error: {e}")


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
            logging.info('weaviate collection created')
            # df = process_and_upload_image_summaries()
            with image_summaries_collection.batch.dynamic() as batch:  # Use the collection variable

                for _, row in df.iterrows():
                    batch.add_object(properties={
                        'file_names': str(row['file_names']),  # str() conversion already handled in DataFrame creation
                        'image_summary': str(row['image_summary']),
                    })

            aggregation = image_summaries_collection.aggregate.over_all(total_count=True)  # Use the collection variable
            total_count = aggregation.total_count
            logging.info(f"Total objects in Weaviate: {total_count}")
            print(f"Total objects in Weaviate: {total_count}")

            return f"Function completed. Total objects in Weaviate: {total_count}"


    except Exception as e:
        print(f"Error interacting with Weaviate: {e}")
        logging.error(f"Weaviate interaction error: {e}")
        return f"Function failed. Weaviate error: {e}"

