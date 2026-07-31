$ErrorActionPreference = "Continue"

$dir = "D:\LUIS\WEBSITE\DOIKITA\doikita"
$python = "C:\Users\WIN 10 PRO\AppData\Local\Programs\Python\Python314\python.exe"
$log = Join-Path $dir "bot.log"

while ($true) {
    cmd /c 'echo === Bot started %date% %time% === >> "D:\LUIS\WEBSITE\DOIKITA\doikita\bot.log"'
    cmd /c '"C:\Users\WIN 10 PRO\AppData\Local\Programs\Python\Python314\python.exe" -u "D:\LUIS\WEBSITE\DOIKITA\doikita\worker.py" >> "D:\LUIS\WEBSITE\DOIKITA\doikita\bot.log" 2>&1'
    cmd /c 'echo === Bot exited code %errorlevel% at %date% %time% - restarting in 10s === >> "D:\LUIS\WEBSITE\DOIKITA\doikita\bot.log"'
    Start-Sleep -Seconds 10
}
