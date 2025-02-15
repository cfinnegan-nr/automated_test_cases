import pandas as pd
import json
from openpyxl import Workbook
import logging


"""
    The AI response has been parsed and the test cases are now available in a JSON format.
    The next step is to convert the JSON data into an Excel file that can be imported into Zephyr. 
    The Excel file should have the following columns: 
        "External id", "Test Summary", "OrderId", "Step", "Test Data", 
        "Expected Result", "Assigned To", "Comments", "Description", "Component", 
        "jira-customfield-checkbox", "Epic Link", "Linked issues", "Labels", "Issue Key [To add steps]".
    The Excel file should be saved as "Zephyr_Test_Cases_Output.xlsx".

    For simplicty, some dummy variabels have been hardcoded in the function. 
    These should be replaced with the actual values or fetched from the environment variables.


"""
def generate_excel_from_json(json_file, epic_link):
    try:
        with open(json_file, 'r') as file:
            data = json.load(file)

        test_cases = data.get('testCases', [])
        wb = Workbook()

        id_counter = 1

        for sheet_index, test_case in enumerate(test_cases, start=1):
            # Create a new sheet for each test case
            if sheet_index == 1:
                ws = wb.active
                ws.title = f"Sheet{sheet_index}"
            else:
                ws = wb.create_sheet(title=f"Sheet{sheet_index}")

            # Set up headers
            headers = [
                "External id", "Test Summary", "OrderId", "Step", "Test Data",
                "Expected Result", "Assigned To", "Comments", "Description", 
                "Component", "jira-customfield-checkbox", "Epic Link", 
                "Linked issues", "Labels", "Issue Key [To add steps]", 
                "Issue Link Type", "Issues Key To Link", "Priority", "Sprint", 
                "Version", "Cascade"
            ]
            ws.append(headers)

            preconditions = test_case.get('preconditions', '')
            postconditions = test_case.get('postconditions', '')
            description = f"{preconditions}\n{postconditions}"

            for order_id, step in enumerate(test_case.get('steps', []), start=1):
                row = [
                    id_counter,  # External id
                    test_case.get('summary', ''),  # Test Summary
                    order_id,  # OrderId
                    step.get('step', ''),  # Step
                    '',  # Test Data (optional, leaving empty)
                    step.get('expectedResult', ''),  # Expected Result
                    "6414a0cd67102fc717c034d7",  # Assigned To
                    "This test case has been built by GenAI Workbench for XL import via Internal Importer.",  # Comments
                    description,  # Description
                    "Core",  # Component
                    "external",  # jira-customfield-checkbox
                    #"INVHUB-10821",  # Epic Link
                    epic_link,  # Epic Link
                    "blocks",  # Linked issues
                    "GenAI_Test_Case",  # Labels
                    "IM-5000",  # Issue Key [To add steps]
                    "blocks",  # Issue Link Type
                    "IM-3000",  # Issues Key To Link
                    "3 - Medium",  # Priority
                    37,  # Sprint
                    "Release-1.0",  # Version
                    "Dublin"  # Cascade
                ]
                ws.append(row)

            id_counter += 1

        # Save the workbook
        output_file = "Zephyr_Test_Cases_Output.xlsx"
        wb.save(output_file)
        logging.info(f"Stage 5b - Excel file '{output_file}' created successfully.")

    except FileNotFoundError:
        print(f"The file '{json_file}' does not exist.")
    except json.JSONDecodeError:
        print("Error decoding JSON. Please check the format of the input file.")
    except Exception as e:
        print(f"An error occurred: {e}")

