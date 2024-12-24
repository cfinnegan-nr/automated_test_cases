# App.py Description

`app.py` is a Python script that interacts with the Jira API to retrieve particular fields from a Jira ticket and then sends these details to an AI model, specifically a GPT-4 model, which generates QA test cases based on the given ticket information.

This test case is then used to build an EXCEL file in a format that can be loaded into JIRA as Zephyr test case using the Zephyr Squad Internal Import utility.

`app.py` takes the JIRA ticket with the requirements as a command line argument, along with a second argument to idenfity the parent EPIC issue type for the new test case in JIRA. The output of the program is an EXCEL with multiple tabs, each representing a different test case scenario.



The script starts off by importing necessary libraries, which include `requests` and `json` among others. 

It then sets JIRA and AI authentication parameters (like the API endpoints, user-names, and API tokens). 

A whitelist is specified to filter the data fetched from the Jira API. This whitelist is a dictionary specifying the keys that should be included in the reduced data.


`app.py` is the main calling function that in turn calls other Python modules;

 - `jiraextraction.py` contains the functions to extract requirement data directly from JIRA through an API call;

        
    - `filter_dict(d, whitelist)` - filters the response from Jira call based on the whitelist.
    - `extract_key(json_response)` - extracts the Jira ticket key from the Jira API response.
    - `retrieve_jira_ticket_from_file(file_name)` - if Jira data is located in a file, this function reads it.
    - `retrieve_jira_ticket_from_server(jira_ticket)` - provides the server call to Jira API to fetch the ticket data.


 - `queryLLM.py` contains the functions to query the AI model;

    - `queryAI(my_prompt)` - sends the reduced Jira ticket information to the AI model and retrieves the response.

        The prompt sent to the LLM is defined external to the code in the text file named `LLM_Prompt.txt`. The prompt can therefore be amended outside of the Python project coce.

        The filtered JIRA data is converted to a JSON string and sent to the AI model to generate the QA test cases. The test case generation process can be deterministic because the temperature parameter is set to 0. These results are created for the user in a readable, indented JSON file format.



 - `Zephyrimport.py` contains the functions to build the EXCEL file for use with Zephyr Squad imports;

    - `generate_excel_from_json(json_file, epic_link)` - breaks down the JSON file with the test case, as created by the LLM, and formats into the appropriate format for a Zephyr Squad import. Multiple Zephyr test cases can be created in a single EXCEL file.





In the main script, a Jira ticket number "INVHUB-11696" has been used as a sample to retrieve the data from the Jira server using `retrieve_jira_ticket_from_server()`. The data is then filtered using the whitelist.






This project is built around a general use case for Investigator Gub. Hence, the test case must be linked to a
specifc EPIC Issue Type in JIRA.

For other projects the code can be amended to suit the specific project requirements.