
import requests
import logging
from requests.auth import HTTPBasicAuth



# Import OpenAI Environment Variables
from openaienvvars import (JIRA_BASE_URL, JIRA_RETRIEVE_ENDPOINT, 
                           JIRA_CREATE_ENDPOINT, JIRA_USER_NAME, JIRA_API_TOKEN)


# Check if the required environment variables are set
def validate_JIRA_env_vars():
    """
    Validate that all required environment variables are set
    """
    if JIRA_USER_NAME == "not_found":
        logging.error("JIRA User Name not set")
        return False
    if JIRA_API_TOKEN == "not_found":
        logging.error("JIRA API Token not set")
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
        error_message = f"Error retrieving JIRA ticket: {e}"
        logging.error(error_message)
        return None
