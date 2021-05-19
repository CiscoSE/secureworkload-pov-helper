# Scripts to help with Cisco Secure Workload PoVs
These scripts help simulate label integrations that would be deployed in a production environment, but may be more difficult to deploy in a 4-week PoV.

## Annotations Optimizer
A very common integration would be IPAM/Infoblox.  This integration helps Cisco Secure Workload determine the "Zone" attributes for a workload.  Is it in the DC?  Is it a User?  Is it in a DMZ?  Often in PoV's, rather than doing a native integration, a user will export, Infoblox data in CSV format to uploade manually into the Secure Workload UI. SaaS PoV's are not full scale, though, and the maximum number of manually uploaded subnets is restricted to 120.  After agents are deployed, this script will take a full CSV input from an IPAM, then it will query Secure Workload to see what IP addresses are relevant for the PoV policy discovery.  It will then output an optimized CSV so that only the relevant subnets are uploaded.

## DNS Helper
This script simulates the native DNS integration.  A first script queries Secure Workload for all of the inventory IPs that need DNS annotations.  This script will often be run by the Cisco architect or partner supporting the PoV.  From that script, a JSON file of IP's is generated.  The JSON file of IPs can be passed to the customer along with a PowerShell script that can be run on any Windows desktop from within the customer environment.  The output of the script will be a CSV that can directly be uploaded to Cisco Secure Workload to provide DNS FQDN as a label.

## Conversations Exporter
This script exports all conversations from a worskpace to a .xlsx format.