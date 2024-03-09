import requests
import csv

API_KEY = 'your_pat_or_sat_token'
ACCOUNT_IDENTIFIER = 'your_account_id'
BASE_URL = 'https://app.harness.io'

headers = {
    'x-api-key': API_KEY,
    'Harness-Account': ACCOUNT_IDENTIFIER
}

def list_organizations():
    print("start list orgs")
    response = requests.get(f'{BASE_URL}/v1/orgs', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch organizations:", response.text)
        return []

def list_projects(org_identifier):
    response = requests.get(f'{BASE_URL}/v1/orgs/{org_identifier}/projects', headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch projects for org {org_identifier}:", response.text)
        return []

def list_role_assignments(account_identifier, org_identifier=None, project_identifier=None):
    params = {
        'accountIdentifier': account_identifier,
        'pageIndex': 0,
        'pageSize': 50  # Adjust as needed
    }
    if org_identifier is not None:
        params['orgIdentifier'] = org_identifier
    if project_identifier is not None:
        params['projectIdentifier'] = project_identifier
    response = requests.get(f'{BASE_URL}/authz/api/roleassignments', headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch role assignments:", response.text)
        print("URL:", response.url)
        return None

def generate_csv(data, filename='role_assignments_summary.csv'):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['Account', 'Organization', 'Project', 'RoleAssignment', 'PrincipalType', 'PrincipalName', 'ResourceGroupIdentifier'])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def main():
    data = []
    # Account-level role assignments
    account_roles = list_role_assignments(ACCOUNT_IDENTIFIER)
    if account_roles and 'data' in account_roles and 'content' in account_roles['data']:
        for role_assignment in account_roles['data']['content']:
            add_role_assignment_data(role_assignment, data, 'NA', 'NA')  # No org or project for account level
    
    orgs_response = list_organizations()
    # print(orgs_response)
    for org in orgs_response:
        org_id = org['org']['identifier']
        org_name = org['org']['name']
        print("Analyzing org name: %s" % org_name)
        # print("org identifier: %s" % org_id)
        # Org-level role assignments
        org_roles = list_role_assignments(ACCOUNT_IDENTIFIER, org_id)
        if org_roles and 'data' in org_roles and 'content' in org_roles['data']:
            for role_assignment in org_roles['data']['content']:
                add_role_assignment_data(role_assignment, data, org_name, 'NA')

        projects = list_projects(org_id)
        if projects:
            for project in projects:
                project_id = project['project']['identifier']
                project_name = project['project']['name']
                print("project name: %s" % project_name)
                print("project identifier: %s" % project_id)
                project_roles = list_role_assignments(ACCOUNT_IDENTIFIER, org_id, project_id)
                if project_roles and 'data' in project_roles and 'content' in project_roles['data']:
                    for role_assignment in project_roles['data']['content']:
                        add_role_assignment_data(role_assignment, data, org_id, project_id)

    generate_csv(data)

def add_role_assignment_data(role_assignment, data_list, org_id, project_id):
    principal_type = role_assignment['roleAssignment']['principal']['type']
    principal_id = role_assignment['roleAssignment']['principal']['identifier']
    # Safely get scopeLevel and ensure it's a string before calling .lower()
    principal_scope_level = role_assignment['roleAssignment']['principal']['scopeLevel']
    principal_scope_level = principal_scope_level.lower() if principal_scope_level else 'account'
    principal_name = 'Unknown'  # Default value in case of failure

    if principal_scope_level == 'unknown':
        print(f"Unknown scopeLevel for principal with ID {principal_id}")
        print("Role Assignment:", role_assignment)
        return
    if principal_id.startswith('_'):
        principal_name = principal_id
    else:
        # Determine the scope for fetching details based on the scopeLevel of the principal
        if principal_scope_level == 'account':
            # Fetch details without org or project scope
            details = fetch_principal_details(principal_type, principal_id, ACCOUNT_IDENTIFIER)
        elif principal_scope_level == 'organization':
            # Fetch details with org scope only
            details = fetch_principal_details(principal_type, principal_id, ACCOUNT_IDENTIFIER, org_id=org_id)
        elif principal_scope_level == 'project':
            # Fetch details with both org and project scope
            details = fetch_principal_details(principal_type, principal_id, ACCOUNT_IDENTIFIER, org_id=org_id, project_id=project_id)
        else:
            # Default case, if scopeLevel is not provided or unrecognized
            # details = {'name': 'Unknown Scope'}
            print(f"Unknown scopeLevel for principal with ID {principal_id}")
            print("Role Assignment:", role_assignment)
            print("principal_scope_level:", principal_scope_level)
            print("principal type:", principal_type)
            details = fetch_principal_details(principal_type, principal_id, ACCOUNT_IDENTIFIER)

        principal_name = details.get('name', 'Details Not Found')

    # Append data for CSV
    data_list.append({
        'Account': ACCOUNT_IDENTIFIER,
        'Organization': org_id if org_id != 'NA' else 'N/A',
        'Project': project_id if project_id != 'NA' else 'N/A',
        'RoleAssignment': role_assignment['roleAssignment']['roleIdentifier'],
        'PrincipalType': principal_type,
        'PrincipalName': principal_name,
        'ResourceGroupIdentifier': role_assignment['roleAssignment'].get('resourceGroupIdentifier', 'N/A')
    })



def fetch_principal_details(principal_type, principal_id, account_identifier, org_id=None, project_id=None):
    # Determine the base URL and parameters based on the principal type
    if principal_type == 'USER':
        url = f'{BASE_URL}/ng/api/user/aggregate/{principal_id}'
    elif principal_type == 'USER_GROUP':
        url = f'{BASE_URL}/ng/api/user-groups/{principal_id}'
    elif principal_type == 'SERVICE_ACCOUNT':
        url = f'{BASE_URL}/ng/api/serviceaccount/aggregate/{principal_id}'
    else:
        print(f"Unknown principal type: {principal_type}")
        return {'name': 'Unknown Principal Type'}

    params = {'accountIdentifier': account_identifier}
    if org_id:
        params['orgIdentifier'] = org_id
    if project_id:
        params['projectIdentifier'] = project_id

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if principal_type in ['SERVICE_ACCOUNT']:
            name = data['data'].get('serviceAccount',{}).get('name', 'Unknown')
        elif principal_type == 'USER':
            name = data['data'].get('user', {}).get('name', 'Unknown')
        elif principal_type == 'USER_GROUP':
            name = data['data'].get('name', 'Unknown')
        else:
            print(f"Unknown principal type: {principal_type}")
            name = 'Unknown'  # Fallback for unexpected cases
        if name == 'Unknown':
            print(f"Failed to fetch details for {principal_type} with ID {principal_id}")
            print("URL:", response.url)
            print("Response:", response.text)
        return {'name': name}
    else:
        print("URL:", response.url)
        print("Response:", response.text)
        print("response.status_code:", response.status_code)
        print(f"Failed to fetch details for {principal_type} with ID {principal_id}: {response.text}")
        print("principal_id:", principal_id)
        print("principal_type:", principal_type)
        print("account_identifier:", account_identifier)
        print("org_id:", org_id)
        print("project_id:", project_id)
        return {'name': 'Details Fetch Failed'}



def get_user_details(user_id, account_identifier, org_identifier=None, project_identifier=None):
    params = {
        'accountIdentifier': account_identifier
    }
    if org_identifier is not None:
        params['orgIdentifier'] = org_identifier
    if project_identifier is not None:
        params['projectIdentifier'] = project_identifier
    response = requests.get(f'{BASE_URL}/ng/api/user/aggregate/{user_id}', headers=headers, params=params)
    # print("URL:", response.request.url)
    if response.status_code == 200:
        data = response.json()
        user_name = data['data']['user'].get('name', 'Unknown')
        return {
            'name': user_name,
            'orgIdentifier': org_identifier,
            'projectIdentifier': project_identifier
        }
    else:
        print("Failed to fetch user details:", response.text)
        print("URL:", response.request.url)
        print("user_id:", user_id)
        return {'name': 'Unknown', 'orgIdentifier': org_identifier, 'project_identifier': project_identifier}

def get_user_group_details(user_group_id, account_identifier, org_identifier=None, project_identifier=None):
    params = {
        'accountIdentifier': account_identifier
    }
    if org_identifier is not None:
        params['orgIdentifier'] = org_identifier
    if project_identifier is not None:
        params['projectIdentifier'] = project_identifier
    
    response = requests.get(f'{BASE_URL}/ng/api/user-groups/{user_group_id}', headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        user_group_name = data['data'].get('name', 'Unknown')  # Assuming 'name' is part of the response
        print("user_group_name:", user_group_name)
        return {
            'name': user_group_name,
            'orgIdentifier': org_identifier,
            'projectIdentifier': project_identifier
        }
    else:
        print("Failed to fetch user group details:", response.text)
        print("URL:", response.url)
        return None

def get_service_account_details(service_account_id, account_identifier, org_identifier=None, project_identifier=None):
    params = {
        'accountIdentifier': account_identifier
    }
    if org_identifier is not None:
        params['orgIdentifier'] = org_identifier
    if project_identifier is not None:
        params['projectIdentifier'] = project_identifier
    
    response = requests.get(f'{BASE_URL}/ng/api/serviceaccount/aggregate/{service_account_id}', headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        service_account_name = data['data'].get('name', 'Unknown')  # Assuming 'name' is part of the response
        return {
            'name': service_account_name,
            'orgIdentifier': org_identifier,
            'projectIdentifier': project_identifier
        }
    else:
        print("Failed to fetch service account details:", response.text)
        print("URL:", response.url)
        return None

if __name__ == "__main__":
    main()
