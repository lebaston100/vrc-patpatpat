@echo off
REM Inbound rule for UDP port 8872
netsh advfirewall firewall add rule name="patpatpat Port 8872 Inbound" dir=in action=allow protocol=UDP localport=8872

REM Outbound rule for UDP port 8871
netsh advfirewall firewall add rule name="patpatpat Port 8871 Outbound" dir=out action=allow protocol=UDP localport=8871

REM Outbound rule for UDP port 8888
netsh advfirewall firewall add rule name="patpatpat Port 8888 Outbound" dir=out action=allow protocol=UDP localport=8888