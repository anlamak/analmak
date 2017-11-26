import ipgetter
import argparse
import ast
from oauth2client.service_account import ServiceAccountCredentials
import googleapiclient.discovery

def getPublicIP():
    return ipgetter.myip()

def connectCompute():
    scopes = ['https://www.googleapis.com/auth/compute.readonly',
            'https://www.googleapis.com/auth/compute',
            'https://www.googleapis.com/auth/cloud-platform']

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        '<PATH_TO_KEYFILE>', scopes)

    return googleapiclient.discovery.build('compute', 'v1', credentials=credentials)


def getFirewallRule(compute, project, name):
    try:
        return compute.firewalls().get(project=project, firewall="geth-allow-" + name).execute()
    except googleapiclient.errors.HttpError as e:
        print(e)  #TODO Parse exception and confirm was actually 404 rule was not found
        return False

def addNewRule(compute, project, name, myIP):
    rule = "geth-allow-" + name
    config = {
        "name": rule,
        "selfLink": "projects/node-186621/global/firewalls/geth-allow-" + name,
        "network": "projects/node-186621/global/networks/default",
        "direction": "INGRESS",
        "priority": 1000,
        "targetTags": [
            "geth"
        ],
        "allowed": [
            {
                "IPProtocol": "all"
            }
        ],
        "sourceRanges": [
            myIP + "/32"
        ]
    }
    print(project)
    return compute.firewalls().insert(
        project=project,
        body=config).execute()

def updateRule(compute, project, name, myIP):
    rule = "geth-allow-" + name
    config = {
        "name": rule,
        "selfLink": "projects/node-186621/global/firewalls/geth-allow-" + name,
        "network": "projects/node-186621/global/networks/default",
        "direction": "INGRESS",
        "priority": 1000,
        "targetTags": [
            "geth"
        ],
        "allowed": [
            {
                "IPProtocol": "all"
            }
        ],
        "sourceRanges": [
            myIP + "/32"
        ]
    }
    return compute.firewalls().update(
        project=project,
        body=config,
        firewall=rule).execute()

def getallowedIP(firewallRule):
    ipString = firewallRule.get("sourceRanges", False)
    if ipString is False:
        return False
    else:
        ipList = ast.literal_eval(str(ipString))
        return ipList[0].replace(" ", "").rstrip(ipList[0][-3:]).upper()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Ensure correct IP whitelisted in GCP')
    parser.add_argument('name', help='first name')
    args = parser.parse_args()

    myIP = getPublicIP()

    compute = connectCompute()
    firewallRule = getFirewallRule(compute, 'node-186621', args.name)
    if firewallRule is False:  # Probably this is the first time you are running this script so the rule doesn't exist
        addNewRule(compute, 'node-186621', args.name, myIP)
        try:
            firewallRule = compute.firewalls().get(project=project, firewall="geth-allow-" + name).execute()
        except googleapiclient.errors.HttpError as e:
            print(e)
            exit(1)

    gcpIP = getallowedIP(firewallRule)

    if gcpIP is False:
        exit(1)  # Shouldn't ever get to this.
    elif gcpIP != myIP:
        print("Allowed gcpIP is not the same as my public IP")
        updateRule(compute, 'node-186621', args.name, myIP)
        print("Rule updated")
        exit(0)  # and compete above
    else:
        print("All's good!")
        exit(0)




















