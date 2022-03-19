# avaya-1100-pdt-tool
Friendly tool for interacting with Avaya 1100 series phones using the PDT interface via SSH.
## Installation
To install the dependencies on an online system:
```
pip install -r requirements
```
To install the dependencies on an offline system:

     [Revised Instructions Coming Soon.]

## Usage
With input file of IP addresses:
```
python3 pdt-tool.py -f sample.csv
```
OR without an input file:
```
python3 pdt-tool.py
```

### Example with Input File
```
----------------------------------------------------
Welcome to the unofficial Avaya 1100 Series PDT Tool
----------------------------------------------------
     SSH User: help   SSH Password: 1234
     Input File: sample.csv
     Total IPs in File: 2
     Log File: pdt-tool-logs/pdt-tool-2022-02-22-2055.log
----------------------------------------------------
Please Choose from the following options:
1 -- Set SSH User/Pass
2 -- Set Custom IP Range
3 -- List IP Addresses
4 -- Ping All IPs
5 -- Get Model, Mac, FW version
6 -- Get Phone Screen and Generate Configs
7 -- Reboot Phones
8 -- Clear All Phone Logs
9 -- Factory Reset Phones
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
     Log File: pdt-tool-logs/pdt-tool-2022-02-22-2053.log
----------------------------------------------------
Please Choose from the following options:
1 -- Set SSH User/Pass
2 -- Set Custom IP Range
3 -- List IP Addresses
4 -- Ping All IPs
5 -- Get Model, Mac, FW version
6 -- Get Phone Screen and Generate Configs
7 -- Reboot Phones
8 -- Clear All Phone Logs
9 -- Factory Reset Phones
0 -- Exit


Enter your choice: 
```
### Example showing the custom IP range being set
```
----------------------------------------------------
Welcome to the unofficial Avaya 1100 Series PDT Tool
----------------------------------------------------
     SSH User: help   SSH Password: 1234
     CUSTOM IP RANGE: 10.0.1.1 to 10.0.1.150
     Total IPs in Range: 150
     Log File: pdt-tool-logs/pdt-tool-2022-02-22-2136.log
----------------------------------------------------
Please Choose from the following options:
1 -- Set SSH User/Pass
2 -- Set Custom IP Range
3 -- List IP Addresses
4 -- Ping All IPs
5 -- Get Model, Mac, FW version
6 -- Get Phone Screen and Generate Configs
7 -- Reboot Phones
8 -- Clear All Phone Logs
9 -- Factory Reset Phones
0 -- Exit


Enter your choice: 
```
