$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot

try {
    $branchName = "hf-deploy"

    git checkout --orphan $branchName

    $frontMatter = @"
---
title: Mortgage Risk Retention Analytics Platform
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: streamlit
sdk_version: "1.37.0"
python_version: "3.11"
app_file: dashboard/streamlit_app.py
pinned: false
---

"@

    $readmeContent = Get-Content README.md -Raw
    Set-Content README.md -Value ($frontMatter + $readmeContent) -NoNewline -Encoding UTF8

    git add -A
    git commit -m "HF deploy snapshot"
    git push hf "$branchName`:main" --force

    git checkout main
    git branch -D $branchName

    Write-Output "HF deploy completed."
}
finally {
    Pop-Location
}
