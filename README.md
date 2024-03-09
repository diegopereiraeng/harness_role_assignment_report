# Harness Role Assignments Parser

This Python script is designed to interact with the Harness API, fetching role assignments across account, organization, and project levels, and compiling a detailed CSV report. It demonstrates how to work with the Harness API to list organizations, projects, and their respective role assignments, including fetching additional details for users, user groups, and service accounts based on their scope level.

## Features

- List all organizations and projects within a specified Harness account.
- Fetch role assignments at the account, organization, and project levels.
- Fetch additional details for principals (users, user groups, service accounts) based on their scope.
- Compile a CSV report with details of role assignments across the account.

## Setup

Replace the placeholder values for `API_KEY` and `ACCOUNT_IDENTIFIER` with your actual API key and account identifier from Harness.

```python
API_KEY = 'your_pat_or_sat_token'
ACCOUNT_IDENTIFIER = 'your_account_id'
BASE_URL = 'https://app.harness.io'
```

Ensure the `requests` library is installed in your Python environment:

```bash
pip install requests
```

## Usage

Run the script using Python:

```bash
python3 parse-role_assignments_report.py
```

The script will print the progress as it fetches data from the Harness API and will generate a CSV file named `role_assignments_summary.csv` in the current directory with the compiled role assignment details.

## Function Descriptions

- `list_organizations()`: Fetches and returns a list of organizations from the Harness account.
- `list_projects(org_identifier)`: Fetches and returns a list of projects for a given organization identifier.
- `list_role_assignments(account_identifier, org_identifier=None, project_identifier=None)`: Fetches and returns role assignments, allowing for filtering by account, organization, and/or project.
- `generate_csv(data, filename='role_assignments_summary.csv')`: Generates a CSV file from the provided data list.
- `add_role_assignment_data(role_assignment, data_list, org_id, project_id)`: Processes a single role assignment and appends it to the data list for CSV generation.
- `fetch_principal_details(principal_type, principal_id, account_identifier, org_id=None, project_id=None)`: Fetches additional details for a principal based on type and scope.

## Note

This script is intended as an example and may need adjustments to fit specific use cases or to accommodate API changes.
