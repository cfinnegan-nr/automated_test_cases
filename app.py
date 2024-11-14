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

ZEPHYR_BASE_URL = "https://api.zephyrscale.smartbear.com/v2"

#AI_ENDPOINT = "https://test-apim-eastus2.azure-api.net/openai-test/openai/deployments/gpt-4-32k/chat/completions?api-version=2024-02-15-preview"
#AI_API_TOKEN = os.getenv('AI_API_TOKEN', "not_found")

# Construct the correct URL
AI_ENDPOINT = f"{AZURE_OPENAI_BASE_PATH}/{AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    
# Define additional parameters for the LLM prompt/response
MAX_TOKENS = 1500
TEMPERATURE = 0

# Set up file name structure for JSON files output/input of Test Cases
sFile_TC_suffix = "_test_case_steps"


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
        error_message = f"Error retrieving JIRA ticket: {e}"
        logging.error(error_message)
        #return {"error": error_message}
        return None


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
    
#def createZephrTicket(summary, description, test_cases_payload, project="CETASKS"):
def createZephyrTicket(summary, description, project="CETASKS"):    
    """
    Create a jira zephyr ticket using Jira REST Endpoint
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

    response = requests.post(JIRA_CREATE_ENDPOINT, 
                             data=json.dumps(payload), 
                             headers=headers, 
                             auth=HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN))

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


def add_test_steps(issue_id, steps):
    """Adds test steps to a test issue"""
    url = f"{ZEPHYR_BASE_URL}/testcases/{issue_id}/teststeps"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    for step in steps:
        payload = {
            "step": step['step'],
            "data": step['data'],
            "result": step['result']
        }
        response = requests.post(url, 
                                 headers=headers,
                                 auth=HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN), 
                                 data=json.dumps(payload))
        
        if response.status_code == 201:
            print(f"Added step '{step['step']}' to test case.")
        else:
            print(f"Failed to add step: {response.text}")




def updateZephyrTicket(issue_key, test_cases_payload):
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
    response = requests.post(zephyr_url, 
                             data=json.dumps(test_cases_payload), 
                             headers=headers, 
                             auth=HTTPBasicAuth(JIRA_USER_NAME, JIRA_API_TOKEN))

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
    Read the json file <test_cases_file>.json and return the contents as a string
    """
    with open(f"{test_cases_file}.json") as f:
        return json.load(f)


def clean_ai_response(response):
    try:

        # Strip out the "json" and "
        if response.startswith("```json") and response.endswith("```"):
            parsed_content = response[7:-3].strip()

                                                         
        # Optionally, load the content as JSON if needed:
        # import json
        # content = json.loads(content)

        return parsed_content
    except KeyError as e:
        logging.error(f"Key error when cleaning AI response: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error when cleaning AI response: {e}")
        return None                                                    




def main(jira_ticket):
    """
    Main function to retrieve and process a JIRA ticket, then query the AI for test cases.
    """
    if validate_env_vars() == False:
        print("Environment variables not set correctly. Exiting.")
        exit()

    # Do not proceed to the LLM if there are any errors 
    bProceedtoLLM = True

    # Define the AI response content
    try:
        # Stage 1: Retrieve and filter the JIRA ticket
        try:
            ticket_data = retrieve_jira_ticket_from_server(jira_ticket)
        except Exception as e:
            logging.error(f"\nError retrieving JIRA ticket: {e}")
            ticket_data = None
        
        if ticket_data is None:
            raise ValueError("\nFailed to retrieve JIRA ticket data.")
        
        try:
            reduced_ticket = filter_dict(ticket_data, WHITELIST)
        except Exception as e:
            logging.error(f"Error filtering JIRA ticket data: {e}")
            reduced_ticket = None
        
        if reduced_ticket is None:
            raise ValueError("Failed to filter JIRA ticket data.")
        
        logging.info("Stage 1 - Jira Retrieval")

        # Stage 2: Convert to JSON and query AI
        try:
            ticket_json_str = json.dumps(reduced_ticket)
        except Exception as e:
            logging.error(f"Error converting ticket data to JSON string: {e}")
            ticket_json_str = None
        
        if ticket_json_str is None:
            raise ValueError("Failed to convert ticket data to JSON string.")

        try:
            query_ai_response = query_ai(ticket_json_str)
        except Exception as e:
            logging.error(f"Error querying AI: {e}")
            query_ai_response = {}
        
        # Continue with further processing of the `query_ai_response` if needed

    except ValueError as ve:
        logging.error(f"Processing halted: {ve}")
        bProceedtoLLM = False

    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    
    #
    # # Stage 3: Parse the LLM response to build a JSON file of test case steps
    #
    if bProceedtoLLM == True:
        logging.info("Stage 2 - AI Retrieval")
        if "choices" in query_ai_response and query_ai_response["choices"]:
            ai_content = query_ai_response["choices"][0]["message"]["content"]
            ai_content = clean_ai_response(ai_content)
            
            try: 
                parsed_ai_content = json.loads(ai_content) 
            except json.JSONDecodeError as e:
                print("JSONDecodeError:", e)
                parsed_ai_content = None  # or handle the error appropriately, e.g., assign an empty dict or similar

            if parsed_ai_content is not None:
                print("\n Successful AI Content:\n")
                print(json.dumps(parsed_ai_content, indent=4)) 
                
                # Write the successful JSON output to a file
                try:
                    file_name = f"{jira_ticket}{sFile_TC_suffix}.json"
                    with open(file_name, 'w') as json_file:
                        json.dump(parsed_ai_content, json_file, indent=4)
                    logging.info(f"JSON output successfully written to {file_name}")
                except IOError as e:
                    logging.error(f"Failed to write JSON output to file: {e}")
            else:
                logging.error("Parsed AI content is not available due to JSON decoding failure.")
                print("\n Failed AI Content:\n")
                print(ai_content)
            
        else:
            logging.error("No valid response from AI")


        #
        # Stage 4: Create a new 'Shell' Zephyr ticket 
        #
        logging.info("Stage 3 - Create Test Case Steps in JSON Format")
        # Create a new string variable for the test cases file name
        test_cases_file_name = JIRA_TICKET + sFile_TC_suffix

        try:
            # Retrieve test cases from the file specified by the new variable
            test_cases_payload = get_test_cases_from_file(test_cases_file_name)
            
            if not isinstance(test_cases_payload, dict) or not test_cases_payload:
                raise ValueError("Test cases payload is either not a dictionary or is empty")

            # Create a new JIRA Zephyr ticket and get its key
            zephyr_ticket_key = createZephyrTicket("AI Test Summary A", "AI Test Description A", "CETASKS") 
            
            if not isinstance(zephyr_ticket_key, str) or not zephyr_ticket_key.strip():
                raise ValueError("Zephyr ticket key is either not a string or is empty")
            
            # If everything is successful
            #print(f"Test cases retrieved and ticket created successfully. Ticket Key: {zephyr_ticket_key}")
            logging.info(f"Stage 4 - Test Cases Retrieved / Zephyr 'Shell' Ticket {zephyr_ticket_key} Created Successfully ")

        except ValueError as ve:
            print(f"Validation error: {ve}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


        #
        # Stage 5: Update Zephyr ticket with the test cases steps
        #
        try:
            #updateZephyrTicket(zephyr_ticket_key, test_cases_payload)
            test_steps = [
                {"step": "Step 1", "data": "Test Data 1", "result": "Expected Result 1"},
                {"step": "Step 2", "data": "Test Data 2", "result": "Expected Result 2"},
                {"step": "Step 3", "data": "Test Data 3", "result": "Expected Result 3"}
    ]
            if zephyr_ticket_key:
                add_test_steps(zephyr_ticket_key, test_steps)
                print(f"Test cases steps added to Zephyr ticket {zephyr_ticket_key} successfully.")
                logging.info(f"Stage 5 - Test Cases Steps Added to Zephyr Ticket {zephyr_ticket_key} Successfully ")
        
        except Exception as e:
            print(f"An error occurred while updating the Zephyr ticket: {e}")
            logging.error(f"An error occurred while updating the Zephyr ticket: {e}")



if __name__ == "__main__":

    # Input the JIRA ticket number
    #JIRA_TICKET = "FCENGX-2846"
    JIRA_TICKET = "INVHUB-11696"
    main(JIRA_TICKET)

    # Create a new string variable for the test cases file name
    #test_cases_file_name = JIRA_TICKET + sFile_TC_suffix

    # Retrieve test cases from the file specified by the new variable
    #test_cases_payload = get_test_cases_from_file(test_cases_file_name)

    # Create a new JIRA Zephyr ticket and get its key
   # zephyr_ticket_key = createZephrTicket("AI Test Summary A", "AI Test Description A", "CETASKS")
#    zephyr_ticket_key = "CETASKS-4205"

#   updateZephrTicket("CETASKS-4205", test_cases_payload)
