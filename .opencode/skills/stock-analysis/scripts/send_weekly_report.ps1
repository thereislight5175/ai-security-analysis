$ProjectRoot = "D:\opencode\ai-security-analysis"
$ScriptPath = "$ProjectRoot\.opencode\skills\stock-analysis\scripts\mailer.py"
$PythonExe = "D:\software\Anaconda\python.exe"

$env:PYTHONIOENCODING = "utf-8"
& $PythonExe $ScriptPath
