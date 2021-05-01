# DNS Helper for Secure Workload PoVs
This script simulates the native DNS integration.  A first script queries Secure Workload for all of the inventory IPs that need DNS annotations.  This script will often be run by the Cisco architect or partner supporting the PoV.  From that script, a JSON file of IP's is generated.  The JSON file of IPs can be passed to the customer along with a PowerShell script that can be run on any Windows desktop from within the customer environment.  The output of the script will be a CSV that can directly be uploaded to Cisco Secure Workload to provide DNS FQDN as a label.

1. Run `get_top_talkers.py` which will output `top_talkers.json`
2. Place `top_talkers.json` and `dns_helper.ps1` on a Windows machine in the same folder in the customer network.  Run `dns_helper.ps1`. Which will output `fqdn.csv`
3. Upload `fqdn.csv` in the "Inventory Upload" in Cisco Secure Workload.

## Step 1: get_top_talkers.py Options
```
$ python3 get_top_talkers.py --help
usage: get_top_talkers.py [-h] --tet_url TET_URL --tet_creds TET_CREDS
                          [--workspace WORKSPACE] [--subnets SUBNETS]

Secure Workload PoV Helper - DNS Get Top Talkers - RUN FIRST

optional arguments:
  -h, --help            show this help message and exit
  --tet_url TET_URL     Tetration URL
  --tet_creds TET_CREDS
                        Tetration API Credentials File
  --workspace WORKSPACE
                        Name of the Target Workspace for Conversations. If
                        multiple workspaces have the same name, this may be
                        random. If not provided, it will default to a
                        workspace for the root scope
  --subnets SUBNETS     Additional subnets other than RFC1918 addresses where
                        resolution is needed, ex: customer-owned public IP
                        space. Provide in a comma separated list in CIDR
                        notation.
CHMCHENR-M-L17K:dns_helper chmchenr$ 
```

## Step 1: get_top_talkers.py Usage Example
Against a root scope workspace:
```
python3 get_top_talkers.py --tet_url=https://sales3.tetrationpreview.com --tet_creds=~/Downloads/api_credentials_sales3.json"
```

Against a specific workspace:
```
python3 get_top_talkers.py --tet_url=https://sales3.tetrationpreview.com --tet_creds=~/Downloads/api_credentials_sales3.json --workspace="ACME:Internal:Datacenter:Invoiocing""
```

Against a specific workspace and including additional public subnets:
```
python3 get_top_talkers.py --tet_url=https://sales3.tetrationpreview.com --tet_creds=~/Downloads/api_credentials_sales3.json --workspace="ACME:Internal:Datacenter:Invoiocing" --subnets="64.100.1.0/24,64.100.2.0/24"
```

## Step 1: get_top_talkers.py Sample Output
```
["10.1.2.3", "10.1.2.4", "10.1.2.5", "10.1.2.6",...]
```

## Step 2: dns_helper.ps1 Usage Example
This should be run from within the same network where agents are deployed for the PoV.  The top_talker.json file from step 1 should be in the same folder.
```
PS /tet-pov-builder/dns_helper> ./dns_helper.ps1

Resolving Unknown IPs
    Processing
    [ooooooooooooooooooo                                                                           ]
    
    10.1.2.3    
```

## Step 3:
`fqdn.csv` can now be uploaded directly to the Secure Workload Portal.