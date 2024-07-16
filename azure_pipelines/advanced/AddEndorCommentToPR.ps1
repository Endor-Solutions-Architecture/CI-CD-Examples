#!/usr/bin/env pwsh

# Feed this script using --output-type=json from endorctl
param(
    [string]$jsonFilePath
)

# See https://learn.microsoft.com/en-us/dotnet/api/microsoft.teamfoundation.sourcecontrol.webapi.commentthreadstatus?view=azure-devops-dotnet
$StatusCode = 1 

# Ensure the JSON file exists
if (-Not (Test-Path -Path $jsonFilePath)) {
    Write-Error "The file '$jsonFilePath' does not exist."
    exit 1
}

# Read the JSON file
try {
    $jsonRawContent = Get-Content -Path $jsonFilePath -Raw
    $jsonContent = $jsonRawContent | ConvertFrom-Json
}
catch {
    Write-Error "Failed to read or convert JSON file: $_"
    exit 1
}

# Bail if no warn or block findings
$PolicyCount = $jsonContent.warning_findings.Count + $jsonContent.blocking_findings.Count
if ($PolicyCount -gt 0) {
    $PolicyName = if ($jsonContent.errors.Count -gt 0) { $jsonContent.errors[0] } elseif ($jsonContent.warnings.Count -gt 0) { $jsonContent.warnings[0] }

    $Markdown = @"
# Endor Labs detected $PolicyCount policy violations associated with this pull request.`n
"@

    $Markdown += @"
## Please review the findings that caused the policy violations.`n
"@

    # Combine warning_findings and blocking_findings into a single collection
    $allFindings = $jsonContent.warning_findings + $jsonContent.blocking_findings

    # Loop through each finding
    foreach ($finding in $allFindings) {
        $package = $finding.spec.target_dependency_package_name
        $dependency = $finding.spec.target_dependency_name
        $ghsa = $finding.spec.finding_metadata.vulnerability.meta.name
        $description = $finding.spec.finding_metadata.vulnerability.meta.description
        $severity = $finding.spec.finding_metadata.vulnerability.spec.cvss_v3_severity.level
        $tags = ($finding.spec.finding_tags -join ", ")
        $categories = ($finding.spec.finding_categories -join ", ")
        $summary = $finding.spec.summary
        $remediation = $finding.spec.remediation

        # Append finding to markdown content
        $Markdown += @"
## 📋 Policy: $PolicyName
- **📥 Package:** $package
- **⤵️ Dependency:** $dependency
- **🚩 ${ghsa}:** $description

### Details

- **Severity:** $severity
- **Tags:** $tags
- **Categories:** $categories
- **Summary:** $summary
- **Remediation:** $remediation

"@
    }

    # Build the JSON body up
    $bodyContent = @{
        comments = @(
            @{
                parentCommentId = 0
                content         = $Markdown
                commentType     = 1
            }
        )
        status   = $StatusCode
    } | ConvertTo-Json -Depth 4

    Write-Debug $bodyContent
    # Post the message to the Pull Request
    # https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull%20request%20threads?view=azure-devops-rest-5.1
    try {
        $url = "$($env:SYSTEM_TEAMFOUNDATIONCOLLECTIONURI)$env:SYSTEM_TEAMPROJECTID/_apis/git/repositories/$($env:BUILD_REPOSITORY_NAME)/pullRequests/$($env:SYSTEM_PULLREQUEST_PULLREQUESTID)/threads?api-version=5.1"
        Write-Output "URL: $url"
        $response = Invoke-RestMethod -Uri $url -Method POST -Headers @{ Authorization = "Bearer $env:SYSTEM_ACCESSTOKEN" } -Body $bodyContent -ContentType "application/json"
        if ($Null -ne $response) {
            Write-Output "** Endor Labs PR Comments Added **"
        }
    }
    catch {
        Write-Error $_
        Write-Error $_.Exception.Message
    }
}
else {
    Write-Output "No policy violations found."
}
