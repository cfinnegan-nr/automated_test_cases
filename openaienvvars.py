# OpenAI Environment Variables
# openaienvvars.py
import os

def load_environment_variables(file_path):
    with open(file_path) as f:
        for line in f:
            name, value = line.strip().split('=', 1)
            os.environ[name] = value

# Load environment variables from the file
load_environment_variables('SNR_Azure_OpenAI_Key.txt')

# Now we can access the environment variables
AZURE_OPENAI_BASE_PATH = os.getenv('AZURE_OPENAI_BASE_PATH')
AI_API_TOKEN = os.getenv('AI_API_TOKEN')
AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME')
AZURE_OPENAI_API_INSTANCE_NAME = os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')