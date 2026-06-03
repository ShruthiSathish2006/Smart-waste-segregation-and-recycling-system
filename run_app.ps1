$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$appPath = Join-Path $PSScriptRoot "app.py"

if (Test-Path $bundledPython) {
    & $bundledPython $appPath
    exit $LASTEXITCODE
}

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand) {
    & $pythonCommand.Source $appPath
    exit $LASTEXITCODE
}

Write-Error "Python runtime not found. Use the bundled Codex runtime or install Python and run app.py."
