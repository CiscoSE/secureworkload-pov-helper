"""
Copyright (c) 2021 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Chris McHenry"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


import json
import argparse
from tetpyclient import RestClient
import pandas as pd
import ipaddress
from tqdm import tqdm
from tempfile import NamedTemporaryFile


def getConversations(workspace):
    conversations = []
    offset = None
    workspace
    req_payload = {
        "version": workspace['latest_adm_version'],
        "dimensions": ["src_ip", "dst_ip", "port"],
        "metrics": ["byte_count", "packet_count"],
        "limit": 5000
    }
    result = rc.post(
        '/conversations/{}'.format(workspace['id']), json_body=json.dumps(req_payload)).json()
    conversations = conversations + result['results']

    if 'offset' in result:
        offset = result['offset']

    while offset != None:
        req_payload['offset'] = offset
        result = rc.post(
            '/conversations/{}'.format(workspace['id']), json_body=json.dumps(req_payload)).json()
        conversations = conversations + result['results']
        if 'offset' in result:
            offset = result['offset']
        else:
            offset = None

    return conversations


"""
Main execution routine
"""
parser = argparse.ArgumentParser(description='Tetration Policy to XLS')
parser.add_argument('--tet_url', help='Tetration URL', type=str)
parser.add_argument('--tet_creds', type=str,
                    help='Tetration API Credentials File')
parser.add_argument('--workspace', type=str, default=None,
                    help='Target Workspace for Conversations')
parser.add_argument('--subnets', type=str, default=None, help='Subnets in comma separated list')
args = parser.parse_args()

rc = RestClient(args.tet_url, credentials_file=args.tet_creds, verify=True)
root_scope = rc.get('/openapi/v1/app_scopes').json()[0]['root_app_scope_id']
workspaces = rc.get('/openapi/v1/applications').json()
global_workspace = [x for x in rc.get(
    '/openapi/v1/applications').json() if x['app_scope_id'] == root_scope]

workspace = None
if args.workspace != None:
    workspace = [x for x in workspaces if x['name'] == args.workspace]
    if len(workspace) > 0:
        workspace = workspace[0]
    else:
        print('No workspace named {} found.  Looking for a compatible global workspace.'.format(
            args.workspace))

if workspace == None and len(global_workspace) > 0:
    workspace = global_workspace[0]
elif workspace == None and len(global_workspace) == 0:
    print('No global workspace found.  Please provide the name of a valid workspace as a script argument or create a workspace in the root scope and run an ADM with Deep Policy Generation checked.  Then attempt to run this script again.')
    exit()

if workspace['latest_adm_version'] == 0:
    print('Please run an ADM target workspace or in the global workspace with Deep Policy Generation checked prior to running this script.')
    exit()

conversations = getConversations(workspace=workspace)
print(len(conversations))
conv_df = pd.DataFrame(conversations)

# Filter Tanium
conv_df = conv_df[conv_df['port'] != '17472']

# Get unique addresses and sort by most bytes transfered
src_addresses = conv_df.groupby(['src_ip'])['byte_count'].sum()
print(len(src_addresses))
dst_addresses = conv_df.groupby(['dst_ip'])['byte_count'].sum()
print(len(dst_addresses))
addresses = pd.DataFrame(src_addresses.add(
    dst_addresses, fill_value=0).sort_values(ascending=False))
addresses.reset_index(inplace=True)
addresses = addresses.rename(columns={'index': 'IP'})
addresses = list(addresses['IP'])

# Filter for RFC1918 and Public Subnets
print(args.subnets)
filtered_addresses = []
additional_subnets = []
for subnet in args.subnets.split(','):
    try:
        additional_subnets.append(ipaddress.ip_network(subnet))
    except:
        print('Invalid subnet passed as argument: {}'.format(subnet))
for address in addresses:
    candidate = ipaddress.ip_address(address)
    if candidate.is_private:
        filtered_addresses.append(address)
    else:
        for subnet in additional_subnets:
            if candidate in subnet:
                filtered_addresses.append(address)

print('Creating seed file "top_talkers.json" based on Tetration inventory with {} IPs.'.format(len(filtered_addresses)))
with open('top_talkers.json', 'w') as f:
    f.write(json.dumps(filtered_addresses))
    f.close()