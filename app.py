import os
import requests
from requests.auth import HTTPBasicAuth
import json
import logging

# Import OpenAI Environment Variables
from openaienvvars import (AZURE_OPENAI_BASE_PATH, AI_API_TOKEN, 
                       AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME, 
                       AZURE_OPENAI_API_INSTANCE_NAME, 
                       AZURE_OPENAI_API_VERSION)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
JIRA_RETRIEVE_ENDPOINT = "https://netreveal.atlassian.net/rest/api/2/issue/{}?fields=description%2Ccomment%2Csummary"
JIRA_CREATE_ENDPOINT = "https://netreveal.atlassian.net/rest/api/2/issue"
JIRA_USER_NAME = os.getenv('JIRA_USER_NAME', "not_found")
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', "not_found")

#AI_ENDPOINT = "https://test-apim-eastus2.azure-api.net/openai-test/openai/deployments/gpt-4-32k/chat/completions?api-version=2024-02-15-preview"
#AI_API_TOKEN = os.getenv('AI_API_TOKEN', "not_found")

# Construct the correct URL
AI_ENDPOINT = f"{AZURE_OPENAI_BASE_PATH}/{AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    

MAX_TOKENS = 800
TEMPERATURE = 0

# Define the whitelist
WHITELIST = {
    "key": True,
    "fields": {
        "summary": True,
        "description": True,
        "comment": {
            "comments": {
                "__array__": {
                    "author": {
                        "displayName": True
                    },
                    "body": True,
                    "updated": True,
                }
            }
        }
    }
}

def validate_env_vars():
    """
    Validate that all required environment variables are set
    """
    if JIRA_USER_NAME == "not_found":
        logging.error("JIRA User Name not set")
        return False
    if JIRA_API_TOKEN == "not_found":
        logging.error("JIRA API Token not set")
        return False
    if AI_API_TOKEN == "not_found":
        logging.error("AI API Token not set")
        return False
    return True

def filter_dict(d, whitelist):
    """
    Recursively filter a dictionary to only include keys in the whitelist.
    """
    result = {}
    for k, v in d.items():
        if k in whitelist:
            if isinstance(v, dict):
                result[k] = filter_dict(v, whitelist[k])
            elif isinstance(v, list) and '__array__' in whitelist[k]:
                result[k] = [filter_dict(elem, whitelist[k]['__array__']) if isinstance(elem, dict) else elem for elem in v]
            else:
                result[k] = v
    return result

def retrieve_jira_ticket_from_file(jira_ticket):
    """
    Read the json file <jira_ticket>.json and return the contents as a sting
    """
    with open(f"{jira_ticket}.json") as f:
        return json.load(f)

    
    
def retrieve_jira_ticket_from_server(jira_ticket):
    """
    Retrieve a JIRA ticket's details from the server using the JIRA REST API.
    """
    url = JIRA_RETRIEVE_ENDPOINT.format(jira_ticket)
    auth = HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN)
    
    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving JIRA ticket: {e}")
        return {}

def query_ai(my_prompt):
    """
    Send the filtered JIRA ticket information to the AI endpoint and retrieve the AI-generated test cases.
    """
    system_prompt = ("You are a Zephr test case expert. Generate detailed QA test cases for each issue identified in the Jira ticket, "
                     "and return all the test cases as a structured JSON object. Include the steps, expected results, and any preconditions or postconditions. ")
    
    request_body = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": my_prompt}
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }

    headers = {
        "Content-Type": "application/json",
        "api-key": AI_API_TOKEN
    }

    try:
        response = requests.post(AI_ENDPOINT, headers=headers, json=request_body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying AI: {e}")
        return {}
    
def createZephrTicket(summary, description, test_cases_payload, project="CETASKS"):
    """
    Create a jira zephr ticket using Jira REST Endpoint
    """
    # Headers for the request
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        "fields": {
            "project": {
                "key": project
            },
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": "Test"
            }
        }
    }

    response = requests.post(JIRA_CREATE_ENDPOINT, data=json.dumps(payload), headers=headers, auth=HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN))

    # Print the response
    issue_key = ""
    
    if response.status_code == 201:
        print("Issue created successfully.")
        issue_key = response.json()['key']
        print(f"Issue key: {issue_key}")

    else:
        print(f"Failed to create issue. Status code: {response.status_code}")
        print(response.json())

    return issue_key


def updateZephrTicket(issue_key, test_cases_payload):
    """
    Create a jira zephr ticket using Jira REST Endpoint
    """
    # Zephyr endpoint to add test cases to an issue
    #zephyr_url = f'https://netreveal.atlassian.net/jira/rest/zapi/latest/testcase/{issue_key}'

    print("zephyr_url is {}".format(zephyr_url))
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    # Make the POST request to add test cases
    response = requests.post(zephyr_url, data=json.dumps(test_cases_payload), headers=headers, auth=HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN))

    # Print the response
    if response.status_code == 200:
        print("Test cases added successfully.")
    else:
        print(f"Failed to add test cases. Status code: {response.status_code}")
        # Handle non-JSON response
        try:
            response_json = response.json()
            print(response_json)
        except requests.exceptions.JSONDecodeError:
            print("Response is not in JSON format.")
            print(response.text)



def get_test_cases_from_file(test_cases_file):
    """
    Read the json file <test_cases_file>.json and return the contents as a sting
    """
    with open(f"{test_cases_file}.json") as f:
        return json.load(f)






def main(jira_ticket):
    """
    Main function to retrieve and process a JIRA ticket, then query the AI for test cases.
    """
    if validate_env_vars() == False:
        print("Environment variables not set correctly. Exiting.")
        exit()

    reduced_ticket = filter_dict(retrieve_jira_ticket_from_server(jira_ticket), WHITELIST)
    
    logging.info("Stage 1 - Jira Retrieval Complete")
    ticket_json_str = json.dumps(reduced_ticket)
    
    query_ai_response = query_ai(ticket_json_str)
    
    logging.info("Stage 2 - AI Retrieval Complete")
    if "choices" in query_ai_response and query_ai_response["choices"]:
        ai_content = query_ai_response["choices"][0]["message"]["content"]
        print(json.dumps(json.loads(ai_content), indent=4))
    else:
        logging.error("No valid response from AI")

if __name__ == "__main__":
    JIRA_TICKET = "FCENGX-2846"
    main(JIRA_TICKET)
#    Retrieve tests cases from sample_test_cases.json
#    test_cases_payload = get_test_cases_from_file("sample_test_cases")

#    zephyr_ticket_key = createZephrTicket("AI Test Summary A", "AI Test Description A", "CETASKS")
#    zephyr_ticket_key = "CETASKS-4205"

#   updateZephrTicket("CETASKS-4205", test_cases_payload)
