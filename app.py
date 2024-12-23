import os
import requests
from requests.auth import HTTPBasicAuth
import json
import logging
import re
import sys

# Import function to generate Excel file used as inout for Zephyr Squad Internal Import utilty
from ZephyrImport import generate_excel_from_json

# Import OpenAI Environment Variables
from openaienvvars import (AZURE_OPENAI_BASE_PATH, AI_API_TOKEN, 
                       AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME, 
                       AZURE_OPENAI_API_INSTANCE_NAME, 
                       AZURE_OPENAI_API_VERSION)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
JIRA_BASE_URL = "https://netreveal.atlassian.net"
JIRA_RETRIEVE_ENDPOINT = "https://netreveal.atlassian.net/rest/api/2/issue/{}?fields=description%2Ccomment%2Csummary"
JIRA_CREATE_ENDPOINT = "https://netreveal.atlassian.net/rest/api/2/issue"
JIRA_USER_NAME = os.getenv('JIRA_USER_NAME', "not_found")
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN', "not_found")



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
    # system_prompt = ("You are a Zephyr test case expert. Generate detailed QA test cases for each issue identified in the Jira ticket, "
    #                  "and return all the test cases as a structured JSON object. Include the steps, expected results, and any preconditions or postconditions. ")
    
    # Define the path to the prompt file
    prompt_file_path = os.path.join(os.path.dirname(__file__), 'LLM_Prompt.txt')

    # Read the contents of the file into a variable
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        system_prompt = file.read()

    # Now system_prompt contains the contents of prompt.txt
    
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
    

def clean_ai_response(response):
    try:
        # print("Response - preparsing...\n.")
        # print(response)    
        # print("\n\n")


        # Strip out the leading and end characters returned in the LLM response
        if response.startswith("```json"):
            # Use regex to find everything after the opening ```json and before the second ```
            match = re.search(r'^```json\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                parsed_content = match.group(1).strip()    
        else:
            print("Failure in parsing LLM response to JSON...\n.")



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

    # Do not proceed to the LLM if there are any errors in JIRA Ticket Data Extraction
    bProceedtoLLM = True

    """
    Set up procedural stages to extract JIRA data, query AI, and parse the AI response
    """
    try:
        # Stage 1: Retrieve and filter the JIRA ticket
        try:
            logging.info("Stage 1 - Extract Ticket Data from JIRA")
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
        


        # Stage 2: Convert to JIRA Ticket data to JSON format
        try:
            logging.info("Stage 2 - Build JSON Object with JIRA Ticket Details")
            ticket_json_str = json.dumps(reduced_ticket)
        except Exception as e:
            logging.error(f"Error converting ticket data to JSON string: {e}")
            ticket_json_str = None
        
        if ticket_json_str is None:
            raise ValueError("Failed to convert ticket data to JSON string.")

        
         # Stage 3: Convert to JSON and query AI
        try:
            logging.info("Stage 3 - Requesting LLM to generate test cases using JIRA input...")
            query_ai_response = query_ai(ticket_json_str)
        except Exception as e:
            logging.error(f"Error querying AI: {e}")
            query_ai_response = {}


    except ValueError as ve:
        logging.error(f"Processing halted: {ve}")
        bProceedtoLLM = False

    except Exception as e:
        logging.error(f"Unexpected error: {e}")

    
    
    # Stage 4: Parse the LLM response to build a JSON file of test case steps
    if bProceedtoLLM == True:
        logging.info("Stage 4 - Parsing LLM Response into JSON Format..")
        if "choices" in query_ai_response and query_ai_response["choices"]:
            ai_content = query_ai_response["choices"][0]["message"]["content"]
            ai_content = clean_ai_response(ai_content)
            
            try: 
                parsed_ai_content = json.loads(ai_content) 
            except json.JSONDecodeError as e:
                print("JSONDecodeError:", e)
                parsed_ai_content = None  # or handle the error appropriately, e.g., assign an empty dict or similar

            if parsed_ai_content is not None:
                                               
                # Write the successful JSON output to a file
                try:
                    file_name = f"{jira_ticket}{sFile_TC_suffix}.json"
                    with open(file_name, 'w') as json_file:
                        json.dump(parsed_ai_content, json_file, indent=4)
                    logging.info(f"Stage 4 - JSON output successfully written to {file_name}")
                except IOError as e:
                    logging.error(f"Failed to write JSON output to file: {e}")
            else:
                logging.error("Parsed AI content is not available due to JSON decoding failure.")
                print("\n Failed AI Content:\n")

            
        else:
            logging.error("No valid response from AI")

        # Stage 5: Parse the JSON file of test case steps into XL format for Zephyr Squad Import    
        logging.info("Stage 5 - Building Excel File for Zephyr Squad Import..")
        try:
            generate_excel_from_json(f"{jira_ticket}{sFile_TC_suffix}.json")
            logging.info("\n Successfully Generated AI Content and Created XL for Zephyr Squad Import\n")
        except Exception as e:
            logging.error(f"Error generating Excel file: {e}")
            print(f"Error generating Excel file: {e}")






if __name__ == "__main__":

    # Input the JIRA ticket number as a command line parameter
    

    # Create a new string variable for the test cases file name
    #test_cases_file_name = JIRA_TICKET + sFile_TC_suffix

    # Retrieve test cases from the file specified by the new variable

    # Build an XL from these test cases to use in Zephyr Squad Internal Import utility
   
    if len(sys.argv) != 2:
        print("Usage: python app.py <json_file>")
    else:
        #JIRA_TICKET = "INVHUB-11696"
        JIRA_TICKET = sys.argv[1]
        main(JIRA_TICKET)