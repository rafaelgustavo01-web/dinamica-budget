param(
  [string]$Root = ".",
  [string]$Stack = "polyglot-monorepo",
  [string]$Personas = "architect"
)

$tpl = Join-Path $Root "_agentic_foundation\templates"
$stackDir = Join-Path $Root "_agentic_foundation\stacks"
$personaDir = Join-Path $Root "_agentic_foundation\personas"

$required = @("CLAUDE.md","AGENTS.md","GEMINI.md","OBJECTIVE.md","STACK_PROFILE.md","PERSONA_PROFILE.md","ORCHESTRATION.md")
foreach ($f in $required) {
  $target = Join-Path $Root $f
  if (-not (Test-Path $target)) {
    Copy-Item (Join-Path $tpl $f) $target -Force
  }
}

$stackFile = Join-Path $stackDir ($Stack + ".md")
if (-not (Test-Path $stackFile)) { throw "Unknown stack: $Stack" }
Copy-Item $stackFile (Join-Path $Root "STACK_PROFILE.md") -Force

$personaList = $Personas.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
$out = @("# PERSONA_PROFILE.md", "")
foreach ($persona in $personaList) {
  $pf = Join-Path $personaDir ($persona + ".md")
  if (-not (Test-Path $pf)) { throw "Unknown persona: $persona" }
  $out += Get-Content $pf
  $out += ""
}
Set-Content -Path (Join-Path $Root "PERSONA_PROFILE.md") -Value $out -Encoding UTF8

Write-Host "Bootstrap complete. Update OBJECTIVE.md if needed."
