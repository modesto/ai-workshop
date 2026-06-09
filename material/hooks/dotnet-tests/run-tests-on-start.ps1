# Run .NET tests at session start and inject results as context

$ErrorActionPreference = 'Continue'

# Read stdin (hook input from Copilot — not used but consumed to be well-behaved)
$null = $input | Out-String

# Run dotnet test on the solution
$testOutput = dotnet test --no-build --logger "console;verbosity=normal" 2>&1 | Out-String

$exitCode = $LASTEXITCODE

# Build a status summary
if ($exitCode -eq 0) {
    $status = "PASSED"
} else {
    $status = "FAILED"
}

# Emit systemMessage so the agent knows the test state at session start
$result = [PSCustomObject]@{
    systemMessage = @"
## .NET Test Suite Status at Session Start: $status

``````
$($testOutput.Trim())
``````

$(if ($exitCode -ne 0) { "WARNING: Tests are currently failing. Review the output above before making changes." } else { "All tests are passing. Baseline is healthy." })
"@
} | ConvertTo-Json -Depth 3

Write-Output $result
exit 0
