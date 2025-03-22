from google.cloud import aiplatform
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    "/Users/siraryanmichael/syncscribe/syncscribe-454510-6b6e3db310f5.json"
)
project_id = "syncscribe-454510"
location = "us-central1"

aiplatform.init(
    project=project_id,
    location=location,
    credentials=credentials
)

from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI
aiplatform.init(
    project="syncscribe-454510",
    location="us-central1",
    credentials=credentials
)

# Use Gemini model instead of text-bison
model = GenerativeModel("gemini-pro")
response = model.generate_content(
    f"Provide insights on this meeting summary: a big zoo"
)
insight = response.text
print("Insight:", insight)