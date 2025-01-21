
from requests.auth import HTTPBasicAuth
import json
import logging
import sys


# Import custom functions to extract JIRA requirements data
from jiraextraction import (retrieve_jira_ticket_from_server, 
                            filter_dict, 
                            validate_JIRA_env_vars)


# Import custom functions to for OpenAI LLm connectivity
from queryLLM import (query_ai, 
                      validate_OpenAI_env_vars, 
                      clean_ai_response)


# Import custom function to generate Excel file used as inout for Zephyr Squad Internal Import utilty
from ZephyrImport import generate_excel_from_json



# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')




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

# Check Environment Variables
def validate_env_vars():
    """
    Validate that all required environment variables are set
    """
    if not validate_JIRA_env_vars():
        return False
    if not validate_OpenAI_env_vars():
        return False
    return True



# Main function to retrieve and process a JIRA ticket, then query the AI for test cases,
# # and finally generate an Excel file for Zephyr Squad Internal Import utility.

# This function is called when the script is run from the command line.
def main(jira_ticket, epic_link):
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
        logging.info("Stage 4a - Parsing LLM Response into JSON Format..")
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
                    logging.info(f"Stage 4b - JSON output successfully written to {file_name}")
                except IOError as e:
                    logging.error(f"Failed to write JSON output to file: {e}")
            else:
                logging.error("Parsed AI content is not available due to JSON decoding failure.")
                print("\n Failed AI Content:\n")

            
        else:
            logging.error("No valid response from AI")

        # Stage 5: Parse the JSON file of test case steps into XL format for Zephyr Squad Import    
        logging.info("Stage 5a - Building Excel File for Zephyr Squad Import..")
        try:
            generate_excel_from_json(f"{jira_ticket}{sFile_TC_suffix}.json", epic_link)
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

    # JIRA: INVHUb-11696
    # EPIC_LINK: INVHUB-10821
   
    if len(sys.argv) != 3:
        print("Usage: python app.py <JIRA_TICKET> <EPIC_LINK>")
    else:
        # The user specifies the JIRA ticket from which to generate test cases
        # The EPIC ticket to be linked is also specified - this is an IH requirement
        JIRA_TICKET = sys.argv[1]
        EPIC_LINK = sys.argv[2]
        main(JIRA_TICKET, EPIC_LINK)