Set ws = CreateObject("Wscript.Shell")
ws.Run "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File ""D:\LUIS\WEBSITE\DOIKITA\doikita\run_worker.ps1""", 0, False
