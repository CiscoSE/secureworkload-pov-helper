# Copyright (c) 2021 Cisco and/or its affiliates.

# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.1 (the "License"). You may obtain a copy of the
# License at

#                https://developer.cisco.com/docs/licenses

# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.


$ips = Get-Content 'top_talkers.json' | Out-String | ConvertFrom-Json
$fqdn = @{}
$counter = 0
foreach ($ip in $ips) {
    $counter++
    Write-Progress -Activity 'Resolving Unknown IPs' -CurrentOperation $ip -PercentComplete (($counter / $ips.count) * 100)
    try{
        $result = Resolve-DnsName -Name $ip -ErrorAction Stop
        $fqdn.Add($ip,$result.NameHost -join ';')
    } Catch {

    }
}
$fqdn.GetEnumerator() |
    Select-Object -Property Key,Value |
        Export-Csv -NoTypeInformation -Path .\fqdn.csv