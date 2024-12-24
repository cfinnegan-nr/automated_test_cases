# Atlassian JIRA and OpenAI Environment Variables
import os

def load_environment_variables(file_path):
    with open(file_path) as f:
        for line in f:
            name, value = line.strip().split('=', 1)
            os.environ[name] = value

# Load environment variables from the file
load_environment_variables('SNR_Azure_OpenAI_Key.txt')

# Load OpenAI environment variables
AZURE_OPENAI_BASE_PATH = os.getenv('AZURE_OPENAI_BASE_PATH')
AI_API_TOKEN = os.getenv('AI_API_TOKEN')
AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME = os.getenv('AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME')
AZURE_OPENAI_API_INSTANCE_NAME = os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION')


# Load JIRA environment variables
JIRA_BASE_URL = "https://netreveal.atlassian.net"
JIRA_RETRIEVE_ENDPOINT = "https://netreveal.atlassian.net/rest/api/2/issue/{}?fields=description%2Ccomment%2Csummary"
JIRA_CREATE_ENDPOINT = "https://netreveal.atlassian.net/rest/api/2/issue"
JIRA_USER_NAME = os.getenv('JIRA_USER_NAME', "not_found")
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', "not_found")