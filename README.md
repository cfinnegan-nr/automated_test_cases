# App.py Description

`app.py` is a Python script that interacts with the Jira API to retrieve particular fields from a Jira ticket and then sends these details to an AI model, specifically a GPT-4 model, which generates QA test cases based on the given ticket information.

The script starts off by importing necessary libraries, which include `requests` and `json` among others. 

It then sets JIRA and AI authentication parameters (like the API endpoints, user-names, and API tokens). 

A whitelist is specified to filter the data fetched from the Jira API. This whitelist is a dictionary specifying the keys that should be included in the reduced data.

A series of functions is included in the script:
- `filter_dict(d, whitelist)` - filters the response from Jira call based on the whitelist.
- `extract_key(json_response)` - extracts the Jira ticket key from the Jira API response.
- `retrieve_jira_ticket_from_file(file_name)` - if Jira data is located in a file, this function reads it.
- `retrieve_jira_ticket_from_server(jira_ticket)` - provides the server call to Jira API to fetch the ticket data.
- `queryAI(my_prompt)` - sends the reduced Jira ticket information to the AI model and retrieves the response.

In the main script, a Jira ticket number "FCENGX-2846" is used to retrieve the data from the Jira server using `retrieve_jira_ticket_from_server("FCENGX-2846")`. The data is then filtered using the whitelist.

The filtered data is then converted to a JSON string and sent to the AI model to generate the QA test cases. The test case generation process can be deterministic because the temperature parameter is set to 0. These results are printed out on the terminal for the user in a readable, indented JSON format.