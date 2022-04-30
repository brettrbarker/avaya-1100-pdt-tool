# avaya-1100-pdt-tool
Friendly tool for interacting with Avaya 1100 series phones using the PDT interface via SSH.
## Installation
To install the dependencies on an online system:
```
pip install -r requirements
```
To install the dependencies on an offline system:

I've included some the dependencies that will work for RHEL7 and RHEL8. If you have a different version that won't work with these, you will need to obtain the dependencies with pip online or through another method.
```
pip3 install --no-index dependencies/rhel7/*
OR
pip3 install --no-index dependencies/rhel8/*
```
## Usage
With input file of IP addresses:
```
python3 pdt_tool.py -f sample.csv
```
OR without an input file:
```
python3 pdt_tool.py
```

### Example with Input File
```
----------------------------------------------------
     SSH User: help   SSH Password: 1234
     Input File: sample.csv
     Total IPs in File: 2
     Log File: pdt-tool-logs/pdt-tool-2022-04-30-1705.log
----------------------------------------------------
Please Choose from the following options:
1 -- Set SSH User/Pass
2 -- Set Custom IP Range
3 -- List IP Addresses
4 -- Ping All IPs
5 -- Perform Actions on Phones
6 -- Factory Reset Phones
0 -- Exit


Enter your choice: 
```
### Example with no input file
Option 2 will need to be used to set a custom IP range. Note: A custom range can be set even if an input file is provided. The custom range will not overwrite the input file itself, but will make it irrelevant.
```
----------------------------------------------------
Welcome to the unofficial Avaya 1100 Series PDT Tool
----------------------------------------------------
     SSH User: help   SSH Password: 1234
     Input File: None
     Total IPs in File: 0
     Log File: pdt-tool-logs/pdt-tool-2022-04-30-1704.log
----------------------------------------------------
Please Choose from the following options:
1 -- Set SSH User/Pass
2 -- Set Custom IP Range
3 -- List IP Addresses
4 -- Ping All IPs
5 -- Perform Actions on Phones
6 -- Factory Reset Phones
0 -- Exit


Enter your choice: 
```
### Example showing the custom IP range being set
```
----------------------------------------------------
Welcome to the unofficial Avaya 1100 Series PDT Tool
----------------------------------------------------
     SSH User: help   SSH Password: 1234
     CUSTOM IP RANGE: 10.0.1.1 to 10.0.1.128
     Total IPs in Range: 128
     Log File: pdt-tool-logs/pdt-tool-2022-04-30-1707.log
----------------------------------------------------
Please Choose from the following options:
1 -- Set SSH User/Pass
2 -- Set Custom IP Range
3 -- List IP Addresses
4 -- Ping All IPs
5 -- Perform Actions on Phones
6 -- Factory Reset Phones
0 -- Exit


Enter your choice: 
```

## Explanation of Options
```
1 -- Set SSH User/Pass
```
Let's you set the SSH username and password used to login to the phone.
```
2 -- Set Custom IP Range
```
Allows the setting of a custom IP range to try to connect to. 
```
3 -- List IP Addresses
```
Will list out all the IP addresses currently set to be acted upon. This is either the list from the input file, the custom range, or the filtered range from the ping command (option 4).
```
4 -- Ping All IPs
```
This option will ping every IP in the current list and show if it is successful or not. After running the command, you are presented with the option to set the list to only the successfully pinged devices.
```
5 -- Perform Actions on Phones
```
New in version 2, option 5 presents you with a sub-menu of items that can be selected and then pressing enter will run all of the selected items at once. Further explanation of these options in the next section below.
```
6 -- Factory Reset Phones
```
WARNING: This option will attempt to factory reset every phone in the list.
```
0 -- Exit
```
Exits the PDT Tool.

### Descriptions of the actions performed by option 5
```
----------------------------------------------------
Welcome to the unofficial Avaya 1100 Series PDT Tool
----------------------------------------------------
     SSH User: help   SSH Password: 1234
     CUSTOM IP RANGE: 10.0.1.1 to 10.0.1.128
     Total IPs in Range: 128
     Log File: pdt-tool-logs/pdt-tool-2022-04-30-1707.log
----------------------------------------------------
Choose actions to perform:
  [*] Acknowledge Login Banner                                                                                                   
  [*] Generate Phone Info CSV (IP, Model, MAC, FW Version)                                                                       
> [*] Get Phone Screen                                                                                                           
  [ ] Generate Autologin Configs                                                                                                 
  [ ] Clear Phone Logs                                                                                                           
  [ ] Reboot Phone                                                                                                               
  [ ] Reboot Phone if stuck logging in                                                                                           
Press <space>, <tab> for multi-selection and <enter> to select and accept 
```

```
> [*] Acknowledge Login Banner
```
This will acknowledge the login banner only if a phone is stuck at a login banner asking the user to press OK. If the phone is not at the login banner, this option does not do anything. This is helpful if you are trying to generate autologin configs that needs to be able to read the screen data after the login banner.
```
> [*] Generate Phone Info CSV (IP, Model, MAC, FW Version) 
```
This option will generate a Comma Separated CSV file with information about the phone including IP address, Model (ex. 1120 vs 1140), MAC address, and firmware version.

** If you also select the "Generated Autologin Configs" option along with the CSV, then the phone numbers on the phone will also be included in the CSV file.

```
> [*] Get Phone Screen
```
This option will do a screen capture of the phone's screen and save it to a file. This is useful for seeing other line keys on the phone or if the phone is stuck at login or another error message.
```
> [*] Generate Autologin Configs
```
This option will generate the MAC address specific files that can be put on a provisioning server to have the phone automatically login to the phone numbers that hte PDT Tool finds on line keys. If the PDT Tool can ssh into the phone, but does not detect any line keys, it will make a blank config file in a separate folder.
```
> [*] Clear Phone Logs
```
This option will clear the two different log files (ECR and SIP) in the phone. This can be useful if other actions are not working correctly.
```
> [*] Reboot Phone
```
This option will reboot all the phones after completing the other selected options.
```
> [*] Reboot Phone if stuck logging in
```
This option will ONLY reboot a phone in the list if it is detected that the phone is stuck trying to login a phone number.

# Donate
If this tool was useful to you, please consider donating. And please open issues for any problems or feature requests you have. I would be happy to try to implement them.

[![Donate](https://img.shields.io/badge/Donate-CashApp-green.svg)](https://cash.app/$brettrbarker) [![Donate](https://img.shields.io/badge/Donate-Venmo-blue.svg)](https://account.venmo.com/u/Brett-Barker-54)
