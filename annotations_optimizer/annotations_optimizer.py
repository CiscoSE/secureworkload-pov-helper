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

def str2bool(v):
    if isinstance(v, bool):
       return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def getConversations(workspace):
    conversations = []
    offset = None
    req_payload = {
                        "version": workspace['latest_adm_version'],
                        "dimensions": ["src_ip", "dst_ip", "port"],
                        "metrics": ["byte_count", "packet_count"],
                        "limit" : 5000
                }
    result = rc.post('/conversations/{}'.format(workspace['id']),json_body=json.dumps(req_payload)).json()
    conversations = conversations + result['results']
    
    if 'offset' in result:
        offset = result['offset']

    while offset != None:
        req_payload['offset']=offset
        result = rc.post('/conversations/{}'.format(workspace['id']),json_body=json.dumps(req_payload)).json()
        conversations = conversations + result['results']
        if 'offset' in result:
            offset = result['offset']
        else:
            offset = None

    return conversations
"""
Main execution routine
"""
parser = argparse.ArgumentParser(description='Secure Workload PoV Helper - Annotations Optimizer')
parser.add_argument('--maxsubnets', type=int, default=120, help='Maximum number of subnet entries allowed in an annotations file for PoV')
parser.add_argument('--maxhosts', type=int, default=6000, help='Maximum number of host entries allowed in an annotations file for PoV')
parser.add_argument('--debug', nargs='?',
                    choices=['verbose', 'warnings', 'critical'],
                    const='critical',
                    help='Enable debug messages.')
parser.add_argument('--tet_url', help='Tetration URL',type=str,required=True)
parser.add_argument('--tet_creds',type=str, help='Tetration API Credentials File',required=True)
parser.add_argument('--annotations_file',type=str, help='Customer Annotations File',required=True)
parser.add_argument('--ip_field',type=str, help='Customer Annotations File',required=True)
parser.add_argument('--fields',type=str,help='Comma Separate List of Important Annotation Fields',required=True)
parser.add_argument("--upload", type=str2bool, nargs='?',
                        const=True, default=False,
                        help="If set, the script will also upload the reduced annotations file to Tetration.")
args = parser.parse_args()

rc = RestClient(args.tet_url,credentials_file=args.tet_creds,verify=True)
root_scope = rc.get('/openapi/v1/app_scopes').json()[0]['root_app_scope_id']
global_workspace = [x for x in rc.get('/openapi/v1/applications').json() if x['app_scope_id']==root_scope]

if len(global_workspace)>0:
    global_workspace = global_workspace[0]
else:
    print('No global workspace found.  Please create a workspace in the root scope and run an ADM with Deep Policy Generation checked.  Then attempt to run this script again.')
    exit()

if global_workspace['latest_adm_version'] == 0:
    print('Please run an ADM in the global workspace with Deep Policy Generation checked prior to running this script.')


print('Downloading conversations for root scope and analyzing top talkers...')
conversations = getConversations(workspace=global_workspace)
conv_df = pd.DataFrame(conversations)

#Filter Tanium
conv_df = conv_df[conv_df['port']!='17472']

#Get unique addresses and sort by most bytes transfered
src_addresses = conv_df.groupby(['src_ip'])['byte_count'].sum()
dst_addresses = conv_df.groupby(['dst_ip'])['byte_count'].sum()
addresses = pd.DataFrame(src_addresses.add(dst_addresses, fill_value = 0).sort_values(ascending=False))
addresses.reset_index(inplace=True)
addresses = addresses.rename(columns = {'index':'address'})

#Load annotations file into Pandas DataFrame
file_type = args.annotations_file.split('.')[-1]
if file_type == 'xls' or file_type == 'xlsx':
    annotations_df = pd.read_excel(args.annotations_file)
elif file_type == 'csv':
    annotations_df = pd.read_csv(args.annotations_file)

#Filter to annotations DataFrame to important columns
fields = args.fields
fields = fields.split(',')
ip_field = args.ip_field
fields = [x.strip() for x in fields]
fields.append(ip_field)
annotations_df = annotations_df[fields]

#Drop items with a null value in the IP column
annotations_df = annotations_df[annotations_df[ip_field].notna()]

#Filter out values in the IP column so that only CIDR subnets are left
subnet_exp = '^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/\d+$'
subnets_df = annotations_df[annotations_df[ip_field].str.match(subnet_exp)]

#Evaluate annotations file for subnet matches
#1. Convert subnets dataframe to dictionary -- yes, i know this is inefficient
subnets = list(subnets_df.T.to_dict().values())

#2. Iterate through each subnet in the annotation file to see if there are any IPs that match
print("Analyzing matching subnets...")
for subnet in tqdm(subnets):
    try:
        subnet_object = ipaddress.IPv4Network(subnet[ip_field])
        subnet['match_count'] = addresses[addresses.apply(lambda x: ipaddress.IPv4Address(x['address']) in subnet_object, axis=1)].byte_count.sum()
    except:
        subnet['match_count'] = 0

#3. Clean up annotations file, sort by highest match count, add Workload field, and export.
final_annotations = pd.DataFrame(subnets)
final_annotations = final_annotations[final_annotations['match_count']>0]
final_annotations = final_annotations.sort_values(['match_count'],ascending=[0]).reset_index().drop(['index','match_count'],axis=1)

#Filter to IP values to find exact host matches
ip_exp = '^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
ip_df = annotations_df[annotations_df[ip_field].str.match(ip_exp)]
ip_annotations = pd.merge(ip_df,addresses,how='inner', left_on=ip_field,right_on='address').sort_values(['byte_count'],ascending=[0]).reset_index().drop(['index','byte_count','address'],axis=1)

#Merge IP annotations and Subnet annotations
final_annotations = pd.concat([final_annotations.truncate(before=0,after=args.maxsubnets),ip_annotations.truncate(before=0,after=args.maxhosts)],sort=False)
final_annotations['Workload'] = True
addresses = addresses.rename(columns = {ip_field:'IP'})

if args.upload == True:
    print("Uploading optimized annotations file to Tetration...")
    final_annotations.to_csv('final_annotations.csv', index=False)
elif args.upload == False:
    print("Saving optimized annotations file to the current folder as 'final_annotations.csv'.")
    final_annotations.to_csv('final_annotations.csv', index=False)