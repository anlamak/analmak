import ipgetter
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
        '.keys/node-3827634af604.json', scopes)

    return googleapiclient.discovery.build('compute', 'v1', credentials=credentials)


def getFirewallRule(compute, project, name):
    return compute.firewalls().get(project=project, firewall=name).execute()


def getallowedIP(firewallRule):
    ipString = firewallRule.get("sourceRanges", False)
    if ipString is False:
        return False
    else:
        ipList = ast.literal_eval(str(ipString))
        return ipList[0].replace(" ", "").rstrip(ipList[0][-3:]).upper()

compute = connectCompute()
firewallRule = getFirewallRule(compute, 'node-186621', 'geth')
myIP = getPublicIP()
gcpIP = getallowedIP(firewallRule)

if gcpIP is False:
    print("gcpIP does not exist")
    pass  # TODO addNewRule(myIP)
elif gcpIP != myIP:
    print("allowed gcpIP is not the same as my public IP")
    pass  # TODO updateRule(myIP)
else:
    print("All's good!")










IP = ipgetter.myip()









