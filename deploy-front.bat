@echo off
robocopy "C:\Dinamica-Budget\app\frontend\dist" "C:\inetpub\DinamicaBudget" /E /IS /IT /IM /NFL /NDL /NJH /NJS
echo Deploy concluido. Exit: %ERRORLEVEL%
