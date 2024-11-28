import requests
import time
import hashlib
import hmac
import base64
import os
from requests.auth import HTTPBasicAuth

# Import OpenAI Environment Variables
from openaienvvars import (AZURE_OPENAI_BASE_PATH, AI_API_TOKEN, 
                       AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME, 
                       AZURE_OPENAI_API_INSTANCE_NAME, 
                       AZURE_OPENAI_API_VERSION)

# Zephyr API credentials
Z_SECRET_KEY = os.getenv('ZEPHYR_SQUAD_API_SECRET_KEY', "not_found")
Z_ACCESS_KEY = os.getenv('ZEPHYR_SQUAD_API_ACCESS_KEY', "not_found")
Z_ACCOUNT_ID = os.getenv('JIRA_ACCOUNT_ID', "not_found")
Z_JWT = os.getenv('ZEPHYR_SQUAD_API_JWT', "not_found")

JIRA_USER_NAME = os.getenv('JIRA_USER_NAME', "not_found")
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', "not_found")

ZAPI_BASE_URL = 'https://prod-api.zephyr4jiracloud.com/v2'
# ZAPI_BASE_URL = 'https://prod-play.zephyr4jiracloud.com/connect'


def validateEnvVars():
    """
    Validate that all required environment variables are set
    """
    if Z_SECRET_KEY == "not_found":
        print("Zephyr Squad API Secret Key not set")
        return False
    if Z_ACCESS_KEY == "not_found":
        print("Zephyr Squad API Access Key not set")
        return False
    if Z_ACCOUNT_ID == "not_found":
        print("Zephyr Squad Account ID not set")
        return False
    if JIRA_USER_NAME == "not_found":
        print("JIRA User Name not set")
        return False
    if JIRA_API_TOKEN == "not_found":
        print("JIRA API Token not set")
        return False
    if Z_JWT == "not_found":
        print("Zephyr Squad JWT not set")
        return False
    return True

def generate_headers(http_method, endpoint):
    expiration = int(time.time()) + 3600  # Token expiration time (1 hour)
    canonical_path = endpoint

    payload = f'{http_method}&{canonical_path}&{expiration}&{Z_ACCOUNT_ID}'
    encoded_secret_key = Z_SECRET_KEY.encode('utf-8')
    digest = hmac.new(encoded_secret_key, payload.encode('utf-8'), hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode('utf-8')

    jwt_token = f'JWT {Z_ACCESS_KEY}:{signature}:{expiration}:{Z_ACCOUNT_ID}'

    # From API call to https://prod-vortexapi.zephyr4jiracloud.com/api/v1/jwt/generate (see OneNote)
    # jwt_token = Z_JWT

    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'zapiAccessKey': Z_ACCESS_KEY,
#        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json'
    }

    return headers

def get_cycles():
    endpoint = '/cycle'
    full_url = f'{ZAPI_BASE_URL}{endpoint}'
    headers = generate_headers('GET', full_url)
    
    response = requests.get(full_url, headers=headers, auth=HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN))
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve cycles: {response.status_code}")
        print(response.text)
        return None

def create_test_case():
    endpoint = '/testcases'
    full_url = f'{ZAPI_BASE_URL}{endpoint}'
#    jwt_token = generate_jwt('POST', endpoint)
    
    headers = generate_headers('POST', full_url)
    
    test_case_payload = {
        "name": "Sample Test Case",
        "projectKey": "CETASKS",
        "description": "This is a sample test case created via API",
        "labels": ["automation", "api"]
    }

    response = requests.post(full_url, headers=headers, json=test_case_payload)

    if response.status_code == 201:
        return response.json()
    else:
        print(f"Failed to create test case: {response.status_code}")
        print(response.text)
        return None

# Execute the function to create a test case
if validateEnvVars() == False:
    print("Environment variables not set correctly. Exiting.")
    exit()

created_test_case = create_test_case()

if created_test_case:
    print("Test case created successfully:")
    print(created_test_case)
else:
    print("Failed to create test case.")



#cycles = get_cycles()

#if cycles:
#    print("Cycles retrieved successfully:")
#    print(cycles)
#else:
#    print("Failed to retrieve cycles.")
