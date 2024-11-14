# ChatGPT
import requests
from requests.auth import HTTPBasicAuth
import json

# Constants
JIRA_BASE_URL = "https://netreveal.atlassian.net"
ZEPHYR_BASE_URL = "https://api.zephyrscale.smartbear.com/v2"  # Zephyr Scale Cloud API base URL
PROJECT_KEY = "CETASKS"
#JIRA_USERNAME = "your-email@example.com"
#JIRA_API_TOKEN = "your-jira-api-token"


JIRA_USERNAME="ciaran.finnegan@netreveal.ai"
JIRA_API_TOKEN="ATATT3xFfGF0VYRX4m0h5phgn_pRcjcUsCQzJ-ybMnwyQZ_Zx-jKstEsTs28byCJNhHFCKtBpQU6brhN34de1EB02vRDNPZa5lHsCapN6Ha7RqoqX-zVBBv0nxpCi8QjKwUToYkg4btWAw_CYWkFBXKUegvSaKCubAbEYXapOuSg3-VrXFBwqZg=8F03C3DF"


# Headers for the API requests
headers = {
    "Authorization": f"Basic {requests.auth._basic_auth_str(JIRA_USERNAME, JIRA_API_TOKEN)}",
    "Content-Type": "application/json"
}

def create_test_issue(summary, description):
    """Creates a new test issue in Jira"""
    url = f"{JIRA_BASE_URL}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {
                "key": PROJECT_KEY
            },
            "summary": summary,
            "description": description,
            "issuetype": {
                "name": "Test"  # Adjust if your Zephyr issue type is named differently
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 201:
        issue_id = response.json()["id"]
        print(f"Test issue created successfully with ID: {issue_id}")
        return issue_id
    else:
        print(f"Failed to create test issue: {response.text}")
        return None

def add_test_steps(issue_id, steps):
    """Adds test steps to a test issue"""
    url = f"{ZEPHYR_BASE_URL}/testcases/{issue_id}/teststeps"
    for step in steps:
        payload = {
            "step": step['step'],
            "data": step['data'],
            "result": step['result']
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 201:
            print(f"Added step '{step['step']}' to test case.")
        else:
            print(f"Failed to add step: {response.text}")

def main():
    # Test details
    test_summary = "Sample Test Case"
    test_description = "This is a test case created via API."
    test_steps = [
        {"step": "Step 1", "data": "Test Data 1", "result": "Expected Result 1"},
        {"step": "Step 2", "data": "Test Data 2", "result": "Expected Result 2"},
        {"step": "Step 3", "data": "Test Data 3", "result": "Expected Result 3"}
    ]
    
    # Create test issue
    issue_id = create_test_issue(test_summary, test_description)
    if issue_id:
        # Add steps if issue created successfully
        add_test_steps(issue_id, test_steps)

if __name__ == "__main__":
    main()
