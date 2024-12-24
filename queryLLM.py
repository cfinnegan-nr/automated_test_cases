
import os
import logging
import re
import requests

# Import OpenAI Environment Variables
from openaienvvars import (AZURE_OPENAI_BASE_PATH, AI_API_TOKEN, 
                       AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME, 
                       AZURE_OPENAI_API_INSTANCE_NAME, 
                       AZURE_OPENAI_API_VERSION)



# Construct the correct URL
AI_ENDPOINT = f"{AZURE_OPENAI_BASE_PATH}/{AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
    
# Define additional parameters for the LLM prompt/response
MAX_TOKENS = 1500
TEMPERATURE = 0


def validate_OpenAI_env_vars():
    """
    Validate that all required environment variables are set
    """
    if AI_API_TOKEN == "not_found":
        logging.error("AI API Token not set")
        return False
    return True    


def query_ai(my_prompt):
    """
    Send the filtered JIRA ticket information to the AI endpoint and retrieve the AI-generated test cases.
    The prompt for the LLM is stored in a text file in the project folder to allow the user to modify it
    outside of the Python function code.
    """
    
    # Define the path to the prompt file
    prompt_file_path = os.path.join(os.path.dirname(__file__), 'LLM_Prompt.txt')

    # Read the contents of the file into a variable
    with open(prompt_file_path, 'r', encoding='utf-8') as file:
        system_prompt = file.read()

    # Now system_prompt contains the contents of LLM_Prompt.txt

    # Construct the request body for the API call to the AI endpoint
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

    # Send the request to the AI endpoint and retrieve the response
    try:
        response = requests.post(AI_ENDPOINT, headers=headers, json=request_body)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error querying AI: {e}")
        return {}
    

def clean_ai_response(response):
    """
    The LLM response will contain other information in addition to the generated test cases.
    This function will parse the response and return only the generated test cases in JSON format.
    """
    
    try:

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

