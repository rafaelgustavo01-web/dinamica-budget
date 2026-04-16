#Requires -RunAsAdministrator
param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$ApiPrefix = "/api/v1",
    [string]$EnvFile = "C:\DinamicaBudget\.env",
    [switch]$UseAuth,
    [string]$OutJson = "C:\Dinamica-Budget\logs\api-routes-validation.json",
    [string]$OutLog = "C:\Dinamica-Budget\logs\api-routes-validation.log"
)

$ErrorActionPreference = "Continue"

$outDir = Split-Path -Parent $OutJson
if (!(Test-Path $outDir)) {
    New-Item -Path $outDir -ItemType Directory -Force | Out-Null
}

function Write-Log([string]$msg) {
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $OutLog -Value $line
}

function Parse-Env([string]$path) {
    $map = @{}
    if (!(Test-Path $path)) { return $map }
    foreach ($raw in Get-Content -Path $path -Encoding UTF8) {
        $line = $raw.Trim()
        if ($line -eq "" -or $line.StartsWith("#")) { continue }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) { continue }
        $k = $line.Substring(0, $idx).Trim()
        $v = $line.Substring($idx + 1).Trim()
        $map[$k] = $v
    }
    return $map
}

function Resolve-Schema($schema, $components) {
    if ($null -eq $schema) { return $null }
    if ($schema.'$ref') {
        $ref = [string]$schema.'$ref'
        if ($ref.StartsWith("#/components/schemas/")) {
            $name = $ref.Replace("#/components/schemas/", "")
            return $components.$name
        }
    }
    if ($schema.oneOf -and $schema.oneOf.Count -gt 0) {
        return Resolve-Schema $schema.oneOf[0] $components
    }
    if ($schema.anyOf -and $schema.anyOf.Count -gt 0) {
        return Resolve-Schema $schema.anyOf[0] $components
    }
    return $schema
}

function New-SampleFromSchema($schema, $components) {
    $resolved = Resolve-Schema $schema $components
    if ($null -eq $resolved) { return $null }

    if ($resolved.enum -and $resolved.enum.Count -gt 0) {
        return $resolved.enum[0]
    }

    $type = [string]$resolved.type
    if ($type -eq "") { $type = "object" }

    switch ($type) {
        "string" {
            $fmt = [string]$resolved.format
            if ($fmt -eq "uuid") { return [guid]::NewGuid().ToString() }
            if ($fmt -eq "email") { return "validator@easymakers.com" }
            if ($fmt -eq "date-time") { return (Get-Date).ToString("o") }
            if ($fmt -eq "date") { return (Get-Date).ToString("yyyy-MM-dd") }
            return "sample"
        }
        "integer" { return 1 }
        "number" { return 1 }
        "boolean" { return $true }
        "array" {
            $item = New-SampleFromSchema $resolved.items $components
            return @($item)
        }
        default {
            $obj = @{}
            $required = @()
            if ($resolved.required) { $required = @($resolved.required) }

            if ($resolved.properties) {
                $propNames = @($resolved.properties.PSObject.Properties.Name)

                if ($required.Count -gt 0) {
                    foreach ($name in $required) {
                        if ($propNames -contains $name) {
                            $obj[$name] = New-SampleFromSchema $resolved.properties.$name $components
                        }
                    }
                } else {
                    foreach ($name in $propNames | Select-Object -First 1) {
                        $obj[$name] = New-SampleFromSchema $resolved.properties.$name $components
                    }
                }
            }

            return $obj
        }
    }
}

function Get-StatusCodeFromException($ex) {
    try {
        if ($ex.Exception.Response -and $ex.Exception.Response.StatusCode) {
            return [int]$ex.Exception.Response.StatusCode
        }
    } catch {}
    return 0
}

function Get-StatusViaCurl([string]$method, [string]$url, [string]$bodyJson) {
    $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
    if (-not $curl) { return 0 }

    $tmpBody = Join-Path $env:TEMP ("route-probe-" + [guid]::NewGuid().ToString() + ".json")
    $args = @("-s", "-o", "NUL", "-w", "%{http_code}", "-X", $method, $url)

    if ($bodyJson -and $method -in @("POST", "PUT", "PATCH")) {
        Set-Content -Path $tmpBody -Value $bodyJson -Encoding UTF8
        $args += @("-H", "Content-Type: application/json", "--data-binary", ("@" + $tmpBody))
    }

    try {
        $out = & curl.exe @args 2>$null
        $code = 0
        [int]::TryParse(([string]$out).Trim(), [ref]$code) | Out-Null
        return $code
    } catch {
        return 0
    } finally {
        Remove-Item -Path $tmpBody -Force -ErrorAction SilentlyContinue
    }
}

Set-Content -Path $OutLog -Value "" -Encoding UTF8
Write-Log "Starting OpenAPI route validation"

$envMap = Parse-Env $EnvFile
$rootEmail = [string]$envMap["ROOT_USER_EMAIL"]
$rootPass = [string]$envMap["ROOT_USER_PASSWORD"]

$headers = @{}
$token = ""

if ($UseAuth -and $rootEmail -and $rootPass) {
    try {
        $loginBody = @{ email = $rootEmail; password = $rootPass } | ConvertTo-Json -Depth 5
        $loginResp = Invoke-RestMethod -Uri "$BaseUrl$ApiPrefix/auth/login" -Method Post -ContentType "application/json" -Body $loginBody -TimeoutSec 10
        $token = [string]$loginResp.access_token
        if ($token) {
            $headers["Authorization"] = "Bearer $token"
            Write-Log "Auth token acquired from ROOT_USER credentials"
        }
    } catch {
        Write-Log "WARN: failed to acquire auth token; protected routes may return 401/403"
    }
} elseif (-not $UseAuth) {
    Write-Log "Running in safe mode without auth token (route reachability, no side effects)"
}

try {
    $openApi = Invoke-RestMethod -Uri "$BaseUrl/openapi.json" -Method Get -TimeoutSec 10
} catch {
    Write-Log "FAIL: cannot fetch openapi.json"
    throw
}

$components = $openApi.components.schemas
$results = New-Object System.Collections.Generic.List[object]
$criticalFailures = 0

foreach ($pathProp in $openApi.paths.PSObject.Properties) {
    $pathTemplate = [string]$pathProp.Name
    $pathNode = $pathProp.Value

    foreach ($methodProp in $pathNode.PSObject.Properties) {
        $method = [string]$methodProp.Name
        if ($method -notin @("get", "post", "put", "patch", "delete")) { continue }

        $op = $methodProp.Value
        $urlPath = $pathTemplate
        $query = @{}

        $parameters = @()
        if ($op.parameters) { $parameters += @($op.parameters) }

        foreach ($p in $parameters) {
            $in = [string]$p.in
            $name = [string]$p.name
            $fmt = ""
            if ($p.schema) { $fmt = [string]$p.schema.format }
            $ptype = ""
            if ($p.schema) { $ptype = [string]$p.schema.type }
            $sample = "sample"
            if ($fmt -eq "uuid" -or $name -match "id$") { $sample = [guid]::NewGuid().ToString() }
            elseif ($ptype -eq "integer") { $sample = 1 }
            elseif ($ptype -eq "number") { $sample = 1 }
            elseif ($name -match "page|limit|offset|size") { $sample = 1 }

            if ($in -eq "path") {
                $urlPath = $urlPath.Replace("{$name}", [string]$sample)
            } elseif ($in -eq "query" -and $p.required -eq $true) {
                $query[$name] = $sample
            }
        }

        $uriBuilder = "$BaseUrl$urlPath"
        if ($query.Count -gt 0) {
            $pairs = @()
            foreach ($k in $query.Keys) {
                $pairs += ("{0}={1}" -f [uri]::EscapeDataString($k), [uri]::EscapeDataString([string]$query[$k]))
            }
            $uriBuilder = ("{0}?{1}" -f $uriBuilder, ($pairs -join "&"))
        }

        $body = $null
        $contentType = "application/json"
        if ($op.requestBody -and $op.requestBody.content) {
            if ($op.requestBody.content.'application/json') {
                $schema = $op.requestBody.content.'application/json'.schema
                $sampleBody = New-SampleFromSchema $schema $components
                $body = $sampleBody | ConvertTo-Json -Depth 12
                $contentType = "application/json"
            }
        }

        $status = 0
        $ok = $false
        $reason = ""
        $errorText = ""

        try {
            $invokeParams = @{
                Uri = $uriBuilder
                Method = $method.ToUpperInvariant()
                TimeoutSec = 10
                ErrorAction = "Stop"
            }

            if ($headers.Count -gt 0) {
                $invokeParams["Headers"] = $headers
            }

            if ($body -ne $null -and $method -in @("post", "put", "patch")) {
                $invokeParams["ContentType"] = $contentType
                $invokeParams["Body"] = $body
            }

            $resp = Invoke-WebRequest @invokeParams
            $status = [int]$resp.StatusCode
            if ($status -lt 500) {
                $ok = $true
                $reason = "reachable"
            } else {
                $ok = $false
                $reason = "server_error"
            }
        } catch {
            $status = Get-StatusCodeFromException $_
            $errorText = [string]$_.Exception.Message
            if ($status -eq 0) {
                $ok = $false
                $reason = "connection_error"
            } elseif ($status -lt 500) {
                $ok = $true
                $reason = "reachable_with_client_status"
            } else {
                $ok = $false
                $reason = "server_error"
            }
        }

        if ($status -eq 0) {
            Start-Sleep -Milliseconds 250
            $fallbackCode = Get-StatusViaCurl $method.ToUpperInvariant() $uriBuilder $body
            if ($fallbackCode -gt 0) {
                $status = $fallbackCode
                if ($status -lt 500) {
                    $ok = $true
                    $reason = "reachable_via_curl_fallback"
                } else {
                    $ok = $false
                    $reason = "server_error_via_curl_fallback"
                }
            }
        }

        if (-not $ok) {
            $criticalFailures += 1
        }

        $item = [pscustomobject]@{
            method = $method.ToUpperInvariant()
            path = $pathTemplate
            resolved_url = $uriBuilder
            status = $status
            ok = $ok
            reason = $reason
            error = $errorText
        }
        $results.Add($item)

        if ($ok) {
            Write-Log ("OK   {0} {1} => HTTP {2} ({3})" -f $item.method, $item.path, $item.status, $item.reason)
        } else {
            Write-Log ("FAIL {0} {1} => HTTP {2} ({3})" -f $item.method, $item.path, $item.status, $item.reason)
        }
    }
}

$summary = [pscustomobject]@{
    base_url = $BaseUrl
    checked_at = (Get-Date).ToString("o")
    total_routes = $results.Count
    critical_failures = $criticalFailures
    healthy = ($criticalFailures -eq 0)
    routes = $results
}

$summary | ConvertTo-Json -Depth 12 | Set-Content -Path $OutJson -Encoding UTF8

if ($criticalFailures -eq 0) {
    Write-Log "Validation complete: all routes reachable without server-side failures"
    exit 0
}

Write-Log "Validation complete: critical failures found ($criticalFailures)"
exit 1
