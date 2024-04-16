Start-Transcript -Append C:\Users\vadim\Desktop\py\logs\OLT_AUTO_WRITE_$(get-date -f yyyy_MM_dd_HH_mm).txt
C:\Users\vadim\Desktop\py\OLT_auto_write_4_beta.exe --path "C:\Users\vadim\Desktop\py\txt\"
Stop-Transcript
Start-Sleep -s 6000