param(
    [Parameter(Mandatory = $true)]
    [int]$MaxNumber
)

$randomNumber = Get-Random -Minimum 1 -Maximum ($MaxNumber + 1)

Write-Host "$randomNumber"