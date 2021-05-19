# Conversations Exporter
At the end of a PoV, the customer may want to keep raw conversation data for reference.  This script will download all conversations from a specific workspace, translate filter IDs to human-readable names, and export into an Excel spreadsheet that could then be analyzed.

## Setup and Prerequisites
```
# clone this repository
git clone https://github.com/CiscoSE/secureworkload-pov-helper.git && cd secureworkload-pov-helper && cd conversations_export

# install dependencies
pip3 install -r requirements.txt
```

## Usage
Command Line Arguments
```
$ python3 conversations_export.py --help
usage: conversations_export.py [-h] --tet_url TET_URL --tet_creds TET_CREDS
                               --workspace WORKSPACE
                               [--exclude_ephemeral_ports]

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
  --exclude_ephemeral_ports
                        Filters out conversations with ports in the standard
                        Windows ephemeral port range. Only ports less than
                        49152 will be included.
```

Example Use
```
$ python3 conversations_export.py --tet_url=https://mycompany.tetrationpreview.com --tet_creds=~/Downloads/api_credentials.json --workspace="Workspace Name" --exclude_ephemeral_ports
```