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