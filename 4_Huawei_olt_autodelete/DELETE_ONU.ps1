Start-Transcript -Append C:\Users\user\Desktop\py\logs\OLT_AUTO_DELETE_$(get-date -f yyyy_MM_dd_HH_mm).txt
C:\Users\user\Desktop\py\OLT_auto_delete.py "C:\Users\user\Desktop\py\ONU_FOR_AUTO_DELETE.txt"
Stop-Transcript
Start-Sleep -s 6000