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
import numpy as np
import ipaddress
from tqdm import tqdm
from tempfile import NamedTemporaryFile


def getConversations(workspace, exclude_ephemeral_ports):
    conversations = []
    offset = None
    workspace
    req_payload = {
        "filter": {
            "type": "eq",
            "field": "excluded",
            "value": False
        },
        "version": workspace['latest_adm_version'],
        "metrics": ["byte_count", "packet_count"],
        "limit": 5000
    }
    if exclude_ephemeral_ports == True:
        req_payload['filter'] = {
            "type": "and",
            "filters": [
                {
                    "type": "eq",
                    "field": "excluded",
                    "value": False
                },
                {
                    "type": "lt",
                    "field": "port",
                    "value": 49152
                }
            ]
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
parser = argparse.ArgumentParser(
    description='Secure Workload PoV Helper - DNS Get Top Talkers - RUN FIRST')
parser.add_argument('--tet_url', help='Tetration URL', type=str, required=True)
parser.add_argument('--tet_creds', type=str,
                    help='Tetration API Credentials File', required=True)
parser.add_argument('--workspace', type=str, default=None, required=True,
                    help='Name of the Target Workspace for Conversations. If multiple workspaces have the same name, this may be random.  If not provided, it will default to a workspace for the root scope')
parser.add_argument('--exclude_ephemeral_ports', action='store_true', default=False,
                    help='Filters out conversations with ports in the standard Windows ephemeral port range.  Only ports less than 49152 will be included.')
args = parser.parse_args()
rc = RestClient(args.tet_url, credentials_file=args.tet_creds, verify=True)

# Find workspace target for exporting conversations
workspaces = rc.get('/openapi/v1/applications').json()
workspace = None
if args.workspace != None:
    workspace = [x for x in workspaces if x['name'] == args.workspace]
    if len(workspace) > 0:
        workspace = workspace[0]
    else:
        print('No workspace named {} found.'.format(
            args.workspace))
        exit()

if workspace['latest_adm_version'] == 0:
    print('Please run an ADM target workspace or in the global workspace with Deep Policy Generation checked prior to running this script.')
    exit()

# Gather scopes and filters and clusters - build dictionary mapping ID (filters) or IP (clusters) to names. Conversation API exports with Filter ID, this will be used to replace with the human readable name.
print('Gathering clusters from workspace...')
workspace_details = rc.get(
    '/openapi/v1/applications/{}/details'.format(workspace['id'])).json()
clusters = workspace_details['clusters']
print('Sucessfully downloaded {} clusters. Gathering scopes...'.format(len(clusters)))
scopes = rc.get('/openapi/v1/app_scopes').json()
print('Sucessfully downloaded {} scopes. Gathering filters...'.format(len(scopes)))
filters = rc.get('/openapi/v1/filters/inventories').json()
print('Sucessfully downloaded {} filters.'.format(len(filters)))
filters = scopes + filters + clusters
name_map = {}
for item in filters:
    name_map[item['id']] = item['name']

for item in clusters:
    for node in item['nodes']:
        name_map[node['ip']] = item['name']

# Get Conversations and load into Pandas DataFrame for processing
print('Gathering conversations for workspace {} version v{}...'.format(
    workspace['name'], workspace['latest_adm_version']))
conversations = getConversations(workspace=workspace,exclude_ephemeral_ports=args.exclude_ephemeral_ports)
print('Downloaded {} conversations.'.format(len(conversations)))
conv_df = pd.DataFrame(conversations)

# Create new columns where ID is replaced with name for "consumer_filter_id", "consumer_filter_ids", "provider_filter_id", "provider_filter_ids"
print('Preparing conversations for export...')
conv_df['consumer_filter_id'] = conv_df['consumer_filter_id'].replace(
    '', np.nan, regex=False)
conv_df['consumer_filter_id'] = conv_df['consumer_filter_id'].fillna(
    conv_df['src_ip'])
conv_df['provider_filter_id'] = conv_df['provider_filter_id'].replace(
    '', np.nan, regex=False)
conv_df['provider_filter_id'] = conv_df['provider_filter_id'].fillna(
    conv_df['dst_ip'])
conv_df['consumer_filter_name_best_match'] = conv_df['consumer_filter_id'].map(
    name_map)
conv_df['provider_filter_name_best_match'] = conv_df['provider_filter_id'].map(
    name_map)

# Export Conversations DataFrame to Excel
print('Exporting to Excel...')
conv_df[['src_ip', 'dst_ip', 'port', 'protocol', 'consumer_filter_name_best_match', 'provider_filter_name_best_match', 'byte_count', 'packet_count']].to_excel(
    '{}-conversations-v{}.xlsx'.format(workspace['name'], workspace['latest_adm_version']))
