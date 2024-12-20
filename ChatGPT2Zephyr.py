import requests
import jwt
import time
import hashlib
from urllib.parse import urlparse



# Zephyr Squad credentials
ACCESS_KEY = "OWRlOWEzOTMtM2Q4Ni0zYjBhLWFlNTMtNDVhOGY4MmIyYjY2IDY0MTRhMGNkNjcxMDJmYzcxN2MwMzRkNyBVU0VSX0RFRkFVTFRfTkFNRQ".strip()  # From Zephyr Squad API Keys
SECRET_KEY = "XFyApljn4qR_hKHGWXq9x86_J3hfzkKsEfmgl7habcY".strip()  # From Zephyr Squad API Keys

# Atlassian credentials
JIRA_USERNAME = "ciaran.finnegan@netreveal.ai"
JIRA_API_TOKEN = "ATATT3xFfGF0VYRX4m0h5phgn_pRcjcUsCQzJ-ybMnwyQZ_Zx-jKstEsTs28byCJNhHFCKtBpQU6brhN34de1EB02vRDNPZa5lHsCapN6Ha7RqoqX-zVBBv0nxpCi8QjKwUToYkg4btWAw_CYWkFBXKUegvSaKCubAbEYXapOuSg3-VrXFBwqZg=8F03C3DF"

# URL for the API call
url = "https://prod-api.zephyr4jiracloud.com/v2/folders?maxResults=10&startAt=0&projectKey=CETASKS&folderType=TEST_CASE"
http_method = "GET"


# HTTP method for the request
http_method = "GET"

def calculate_qsh(http_method, url):
    """
    Calculate the Query String Hash (qsh) for Zephyr Squad.
    """
    parsed_url = urlparse(url)
    canonical_path = parsed_url.path
    query = parsed_url.query

    # Concatenate method, path, and query string
    qsh_string = f"{http_method.upper()}&{canonical_path}&{query}"
    print(f"QSH String: {qsh_string}")

    # Hash the qsh_string using SHA256
    qsh_hash = hashlib.sha256(qsh_string.encode()).hexdigest()
    return qsh_hash

def generate_zephyr_jwt(http_method, url, access_key, secret_key):
    """
    Generate a JWT token for Zephyr Squad API authentication.
    """
    qsh = calculate_qsh(http_method, url)
    print(f"QSH: {qsh}")

    payload = {
        "sub": access_key,
        "qsh": qsh,
        "iss": access_key,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }

    print(f"JWT Payload: {payload}")

    token = jwt.encode(payload, secret_key, algorithm="HS256")
    print(f"Generated JWT: {token}")
    return token

# Generate JWT token
jwt_token = generate_zephyr_jwt(http_method, url, ACCESS_KEY, SECRET_KEY)

# Set headers
headers = {
    "Authorization": f"JWT {jwt_token}",
    "zapiAccessKey": ACCESS_KEY,
    "Content-Type": "application/json"
}

# Make the API request
response = requests.get(url, headers=headers)

# Output response
print(f"Status Code: {response.status_code}")
print(f"Response Text: {response.text}")