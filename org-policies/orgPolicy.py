from oauth2client.client import GoogleCredentials
import json
import googleapiclient.discovery
import subprocess

# Settings:
_path_to_gcloud = "<FULL-PATH-TO-GCLOUD>"
_org = "<ORG-ID>"  # Org ID
_data_folder = "<FOLDER-ID>"  # Folder ID
_non_data_folder = "<FOLDER-ID>"  # Folder ID
_project1 = "<PROJECT-ID>"
#+++++++++++++++++++++++++++++++
_constraint = {
    "constraint": "constraints/serviceuser.services"
}
#+++++++++++++++++++++++++++++++

def connect():
    return GoogleCredentials.get_application_default()

def getCloudResourceManager(credentials):
    return googleapiclient.discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

def enableComputeEngineApi(project):
    return subprocess.check_output([_path_to_gcloud, 'beta', 'service-management', 'enable', 'compute.googleapis.com', '--project=' + project])

def disableComputeEngineApi(project):
    return subprocess.check_output([_path_to_gcloud, 'beta', 'service-management', 'disable', 'compute.googleapis.com', '--project=' + project])

def enableDataprocApi(project):
    return subprocess.check_output([_path_to_gcloud, 'beta', 'service-management', 'enable', 'dataproc.googleapis.com', '--project=' + project])

def disableDataprocApi(project):
    return subprocess.check_output([_path_to_gcloud, 'beta', 'service-management', 'disable', 'dataproc.googleapis.com', '--project=' + project])


def getEnabledApis(project):
    return subprocess.check_output([_path_to_gcloud, 'beta', 'service-management', 'list', '--project=' + project])

def getOrgPolicy(crm, type, resource, body):
    if type.lower() == "project":
        return crm.projects().getOrgPolicy(resource=resource, body=body, x__xgafv=None)
    if type.lower() == "organization":
        return crm.organizations().getOrgPolicy(resource=resource, body=body, x__xgafv=None)
    if type.lower() == "folder":
        return crm.folders().getOrgPolicy(resource=resource, body=body, x__xgafv=None)

def getEffectiveOrgPolicy(crm, type, resource, body):
    if type.lower() == "project":
        return crm.projects().getEffectiveOrgPolicy(resource=resource, body=body, x__xgafv=None)
    if type.lower() == "organization":
        return crm.organizations().getEffectiveOrgPolicy(resource=resource, body=body, x__xgafv=None)
    if type.lower() == "folder":
        return crm.folders().getEffectiveOrgPolicy(resource=resource, body=body, x__xgafv=None)

def setOrgPolicy(crm, type, resource, body):
    if type.lower() == "project":
        return crm.projects().setOrgPolicy(resource=resource, body=body, x__xgafv=None)
    if type.lower() == "organization":
        return crm.organizations().setOrgPolicy(resource=resource, body=body, x__xgafv=None)
    if type.lower() == "folder":
        return crm.folders().setOrgPolicy(resource=resource, body=body, x__xgafv=None)

def checkPolicies(crm, org, folder, project, body):
    orgPolicy = getOrgPolicy(crm, "organization", "organizations/" + org, body=body).execute()
    print "The Current Org Policy is:\n"
    print json.dumps(orgPolicy, indent=4, sort_keys=True)

    folder_OrgPolicy = getOrgPolicy(crm, "folder", "folders/" + folder, body=body).execute()
    print "The Current Org Policy on the Folder is:\n"
    print json.dumps(folder_OrgPolicy, indent=4, sort_keys=True)

    folder_effectiveOrgPolicy = getEffectiveOrgPolicy(crm, "folder", "folders/" + folder, body=body).execute()
    print "The Effective Org Policy on the Folder is:\n"
    print json.dumps(folder_effectiveOrgPolicy, indent=4, sort_keys=True)

    project_orgPolicy = getOrgPolicy(crm, "project", "projects/" + project, body=body).execute()
    print "The Current Org Policy on the Project is:\n"
    print json.dumps(project_orgPolicy, indent=4, sort_keys=True)

    project_effectiveOrgPolicy = getEffectiveOrgPolicy(crm, "project", "projects/" + project,
                                                       body=body).execute()
    print "The Effective Org Policy on the Project is:"
    print json.dumps(project_effectiveOrgPolicy, indent=4, sort_keys=True)

def checkApis(project):
    print "The APIs Enabled on " + project + ":"
    print getEnabledApis(project)



if __name__ == "__main__":

    session = connect()
    crm = getCloudResourceManager(session)

    '''
    # Apply Org Policy
    with open('compute-denied-policy.json') as org_policy:
        data = json.load(org_policy)
        setOrgPolicy(crm, "organization", "organizations/" + _org, body=data).execute()

    # Apply Folder Policy
    with open('compute-allowed-policy.json') as folder_policy:
        data = json.load(folder_policy)
        setOrgPolicy(crm, "folder", "folders/" + _data_folder, body=data).execute()

    # Apply Project Policy
    with open('reset-default.json') as folder_policy:
        data = json.load(folder_policy)
        setOrgPolicy(crm, "folder", "folders/" + _data_folder, body=data).execute()
    '''
    checkPolicies(crm, _org, _data_folder, _project1, _constraint)
    checkApis(_project1)
    '''
    print disableComputeEngineApi(_project1)
    print enableComputeEngineApi(_project1)
    print disableDataprocApi(_project1)
    print enableDataprocApi(_project1)
    '''
