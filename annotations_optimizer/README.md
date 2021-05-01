## Annotations Optimizer
A very common integration would be IPAM/Infoblox.  This integration helps Cisco Secure Workload determine the "Zone" attributes for a workload.  Is it in the DC?  Is it a User?  Is it in a DMZ?  Often in PoV's, rather than doing a native integration, a user will export, Infoblox data in CSV format to uploade manually into the Secure Workload UI. SaaS PoV's are not full scale, though, and the maximum number of manually uploaded subnets is restricted to 120.  After agents are deployed, this script will take a full CSV input from an IPAM, then it will query Secure Workload to see what IP addresses are relevant for the PoV policy discovery.  It will then output an optimized CSV so that only the relevant subnets are uploaded.

# Usage
Command Line Arguments
```
$ python3 annotations_optimizer.py --help

Secure Workload PoV Helper - Annotations Optimizer

optional arguments:
  -h, --help            show this help message and exit
  --maxsubnets MAXSUBNETS
                        Maximum number of subnet entries allowed in an
                        annotations file for PoV
  --maxhosts MAXHOSTS   Maximum number of host entries allowed in an
                        annotations file for PoV
  --debug [{verbose,warnings,critical}]
                        Enable debug messages.
  --tet_url TET_URL     Tetration URL
  --tet_creds TET_CREDS
                        Tetration API Credentials File
  --annotations_file ANNOTATIONS_FILE
                        Customer Annotations File
  --ip_field IP_FIELD   Customer Annotations File
  --fields FIELDS       Comma Separate List of Important Annotation Fields
  --upload [UPLOAD]     If set, the script will also upload the reduced
                        annotations file to Tetration.
```