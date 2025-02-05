import vertexai
from io import BytesIO
from vertexai.generative_models import Part, GenerativeModel
from google.cloud import storage

# Replace with your project ID, bucket name, and blob name (image file name).
project_id = "copper-index-447603-b3"  # your-project-id
bucket_name = "ai-image-cloudfn"  # your-gcs-bucket-name
blob_name = "CamScanner Answer.jpg"  # path/to/image/in/bucket.jpg

vertexai.init(project=project_id, location="us-east1")
model = GenerativeModel(model_name="gemini-1.0-pro-vision-001")

# Initialize a GCS client
storage_client = storage.Client(project=project_id)

try:
    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    # Get the blob (image file)
    blob = bucket.blob(blob_name)
    # Download the image data as bytes
    im_bytes = BytesIO(blob.download_as_bytes())

    image_part = Part.from_data(
        im_bytes.getvalue(),
        mime_type='image/png'  # Adjust mime_type if necessary (e.g., 'image/png')
    )

    query = "Generate a detailed summary of this image for a blind person"
    response = model.generate_content(
        [image_part, query]
    )

    for candidate in response.candidates:
        print(f"Response: {candidate.text}")

except Exception as e:
    print(f"Error: {e}")