#!/usr/bin/env python3
################### AVAYA 1100 SERIES PDT TOOL ######################
## Python tool to easily integrate with an Avaya 1100 series PDT menu via SSH.
## Input CSV with at least columns: IP
## 
## Requires Python 3. For older linux versions with both, use "python3" to initiate script.
##
## USAGE: python3 pdt-tool.py -f [csv input file]
## EXAMPLE: python3 pdt-tool.py -f sample-csv.csv
## 
## Version: 2.0.1
## Updated: 2022-04-30
## Author: Brett Barker - brett.barker@brbtechsolutions.com 
##
## CHANGELOG:
## 1.4.0 - Added Ping option to ping a range of IP addresses and return True/False
## 1.4.1 - Added ability to recycle successful ping results as the new IP list. Will also look for "Ping"
##         as a header in the input file and ask if you only want to use "True" values.
## 1.5.0 - Added feature to get phone screen data using reportWindowData command
## 1.5.1 - Added IP validation to input file IP addresses
## 1.5.2 - Added MAC address to reportWindowData file. 
##         Added wait timers to all SSH invokes to try to increase reliability.
## 1.5.3 - Added sleep timer after factory reset
## 1.5.4 - Improved error exception handling.
##         Fixed bug with not closing client on failed attempt.
## 1.6.0 - Ignore all host keys and accept them no matter what.
## 1.6.1 - Major addition. Option 6 can now generate the phone config files based on phone numbers detected in screen grab.
## 1.6.2 - Fixed dates on output files. 
##         Options can be run more than once without exiting and won't overwrite as long as not started within the same minute.
##         Set phone config file to overwrite previous.
## 1.6.3 - Made the detected line key a minimum of 3 digits.    
## 1.6.4 - Now writes blank config files for successful screen grabs that don't detect a line key.
## 2.0.0.alpha1 - New multi select sub menu to choose multiple actions to perform at once.
## 2.0.0.alpha1 - adds phone nubmers to CSV if generate confige also selected.
## ******* Taking version 2 out of alpha
## 2.0.1 - Added 1 second timeout to ping command. Returns faster from failed pings. 
##
########################################BRB####################################################

from simple_term_menu import TerminalMenu
from paramiko import SSHClient
import time
import csv
import datetime
import re
import datetime
from os import system, name, makedirs, path
from pathlib import Path
from collections import defaultdict, OrderedDict
import netaddr
import logging
import paramiko; logging.basicConfig();




#GLOBAL VARIABLES
SSH_Username = 'help'   # Default value if not changed in user prompt. Can be modified here.
SSH_Pass = '1234'       # Default value if not changed in user prompt. Can be modified here.

# Generated Config file defaults
defaultPassword = '123456'  #  SET THE DEFAULT PASSWORD FOR THE PHONE ACCOUNTS TO LOGIN WITH HERE
defaultDomain = 'example.org' # SET THE DOMAIN AT THE END OF THE PHONE NUMBER USER ACCOUNT

inputfile = ''
success_hosts = []
fail_hosts = []
numSuccess = 0
numFail = 0
IPSet = set()
now = datetime.datetime.now()
#output_csv = 'phone-info-' + now.strftime('%Y-%m-%d-%H%M') + '.csv'
#windowData_file = 'window-data-' + now.strftime('%Y-%m-%d-%H%M') + '.txt'
results_file_name = 'pdt-tool-' + now.strftime('%Y-%m-%d-%H%M') + '.log'
outputpath = "pdt-tool-logs"
results_file = ''
startIP = ''
endIP = ''
customIPs = False
customPingIPs = False

#Multi-select menu actions
# performActionsDict = {
#     'do_acknowledge_banner': False,
#     'do_generate_csv': False,
#     'do_get_screen': False,
#     'do_generate_confg': False,
#     'do_clear_logs': False,
#     'do_reboot': False,
#     'do_reboot_ifstuck': False
# }

# Uncomment to turn on debug logging
#logging.getLogger('paramiko').setLevel(logging.DEBUG) 

menu_options = {
    1: 'Set SSH User/Pass',
    2: 'Set Custom IP Range',
    3: 'List IP Addresses',
    4: 'Ping All IPs',
    5: 'Perform Actions on Phones',
    6: 'Factory Reset Phones',
    0: 'Exit',
}

resultsDict = {
    'Login Banners Acknowledged' : 0,
    'CSVs Generated' : 0,
    'Phone Screens Saved to File' : 0,
    'Autologin Configs Generated' : 0,
    'Phone Logs Cleared' : 0,
    'Phones Rebooted' : 0
}

class IgnorePolicy(paramiko.MissingHostKeyPolicy):
    """
    Policy for ignoring an unknown host key and
    accepting it. This is used by `.SSHClient`.
    """

    def missing_host_key(self, client, hostname, key):
        pass

def print_menu_header():
    print('----------------------------------------------------')
    print('Welcome to the unofficial Avaya 1100 Series PDT Tool')
    print('----------------------------------------------------')
    print('     SSH User: ' + SSH_Username + '   SSH Password: ' + SSH_Pass)
    if not customIPs and not customPingIPs:
        print('     Input File: ' + inputfile)
        print('     Total IPs in File: ' + str(len(IPSet)))
    elif customIPs and not customPingIPs:
        print('     CUSTOM IP RANGE: ' + str(startIP) + ' to ' + str(endIP))
        print('     Total IPs in Range: ' + str(len(IPSet)))
    else:
        print('     CUSTOM IP RANGE: SUCCESSFUL PINGS')
        print('     Total IPs in Range: ' + str(len(IPSet)))
    print('     Log File: ' + outputpath + '/' + results_file_name)
    print('----------------------------------------------------')

def print_menu():
    print_menu_header()
    print('Please Choose from the following options:')
    for key in menu_options.keys():
        print (key, '--', menu_options[key] )

def set_ssh_creds():
    global SSH_Username
    global SSH_Pass
    global success_hosts
    global fail_hosts
    ## PROMPT FOR SSH CREDENTIALS
    new_ssh_user = input('Enter SSH Username: [' + SSH_Username + ']: ')
    new_ssh_pass = input('Enter SSH Password: [' + SSH_Pass + ']: ')
    if new_ssh_user:
        SSH_Username = new_ssh_user
        print('New SSH User set: ' + SSH_Username)
    if new_ssh_pass:
        SSH_Pass = new_ssh_pass
        print('New SSH Password set: ' + SSH_Pass)

def set_ip_range():
    global IPSet
    global customIPs
    global startIP
    global endIP
    clear()
    print('Set a new IP address range')
    startIP = input('Start IP: ')
    try: 
        netaddr.IPAddress(startIP)
    except:
        print('Not a Valid IP Address')
        startIP = ''
        time.sleep(2)
        return
    endIP = input('End IP [' + startIP +']: ')
    if not endIP:
        endIP = startIP
    try: 
        netaddr.IPAddress(endIP)
    except:
        print('Not a Valid IP Address')
        endIP = ''
        time.sleep(2)
        return
    ips = netaddr.iter_iprange(startIP,endIP)
    iplist= list(ips)
    IPSet = [str(x) for x in iplist]
    customIPs = True
    print('Custom IP Range Set.')
    print (startIP + ' to ' + endIP)
    time.sleep(2)

def mainActions(Local_IPSet, performActionsDict):

# Generic setup data
    clear()
    clear_results()
    print_menu_header()
    countIPs = len(Local_IPSet)
    now = datetime.datetime.now()
    phoneInfoList = defaultdict(list)
    global defaultDomain
    global defaultPassword
    windowData_file = 'window-data-' + now.strftime('%Y-%m-%d-%H%M') + '.txt'
    genConfig = False
    phoneNums = []

# Prep Info for Auto Login Configs
    if performActionsDict['do_generate_confg']:
        genConfig = True
        ## PROMPT FOR DOMAIN and Password for Phone Configs
        print('The Following Information is used for the Phone AutoLogin Config Files.')
        new_domain = input('Enter Phone Domain: [' + defaultDomain + ']: ')
        new_user_pass = input('Enter User Password: [' + str(defaultPassword) + ']: ')
        if new_domain:
            defaultDomain = new_domain
            print('New Domain set: ' + defaultDomain)
        if new_user_pass:
            defaultPassword = new_user_pass
            print('New User Password set: ' + defaultPassword)

        proceed = input('PROCEED? y/N: ')
        if not proceed.upper() == 'Y':
            cancel()
            return

    if performActionsDict['do_get_screen']:
        outputpath = "output_files"
        makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.
        f_grab = open(outputpath + '/' + windowData_file, 'w')

    clear()
    print('Running Actions... Please Wait')
 
    # Loop through ALL IP's and perform actions:
    for ip in Local_IPSet:
# MAIN TRY 
        try:
            window = False # set window to false for each IP before possible screen grab
            bannercheck = False
            banner = False
            stucklogin = False
            rebootStuck = False
            # Set up client and connect
            client = SSHClient()
            client.set_missing_host_key_policy(IgnorePolicy)
            client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

            # Open Shell on Client
            chan = client.invoke_shell()
            while not chan.recv_ready():
                time.sleep(1)
            out = chan.recv(9999)
            ## GET Phone Info
            m = re.search('.*connected to (.*). \r\r\nHW ID     :.*\r\nRAM size  :.*\r\nHW version.*\r\nFW version: (.*)\r\nMAC Address = (.*)\r\nIP', out.decode("ascii"))
            phoneModel = m.group(1)
            phoneFirmware = m.group(2)
            phoneMAC = m.group(3)
            phoneInfoList[ip] = [phoneModel, phoneFirmware, phoneMAC]

            # Check for Login Banner or Stuck Logging In
            if performActionsDict['do_acknowledge_banner'] or performActionsDict['do_reboot_ifstuck']:
                chan.send('reportWindowData\n')
                while not chan.recv_ready():
                    time.sleep(3)
                bannercheck = chan.recv(9999)
                for line in bannercheck.decode("ascii").splitlines():
                        if performActionsDict['do_acknowledge_banner']:
                            banner = re.search("----\[Login Banner\] *, <Context>", line)
                        if performActionsDict['do_reboot_ifstuck']:
                            stucklogin = re.search("----\[Logging in user ...     \] *, <InfoLine#1>,", line)
                        if stucklogin:
                            print('+ STUCK LOGGING IN DETECTED')
                            rebootStuck = True
                        if banner: # if Loginbanner is seen, press Ok and call config again
                            print('+ SUCCESS: Cleared Login Banner on ' + str(ip))
                            resultsDict['Login Banners Acknowledged'] += 1
                            chan.send('sendKey 115 2\n') # Press OK button (SoftKey1)
                            while not chan.recv_ready():
                                time.sleep(3)
                            out = chan.recv(9999)


            # Screen Grab Command for Window data file or auto login configs
            if performActionsDict['do_get_screen'] or performActionsDict['do_generate_confg']:
                chan.send('reportWindowData\n')
                while not chan.recv_ready():
                    time.sleep(3)
                window = chan.recv(9999)
                if performActionsDict['do_get_screen']:
                    resultsDict['Phone Screens Saved to File'] += 1
                    print('+ SUCCESS: Grabbed screen info for ' + str(ip) + '!')
 
            ## Clear Logs
            if performActionsDict['do_clear_logs']:
                ecrCleared = False
                sipCleared = False
                ## CLEAR LOG 0
                chan.send('clearlog 0\n')
                while not chan.recv_ready():
                    time.sleep(3)
                out = chan.recv(9999)
                if 'cleared' in out.decode("ascii"):
                    print('+ SUCCESS: Cleared ECR Log File for ' + str(ip) + '!')
                    ecrCleared = True
                ## CLEAR LOG 1
                chan.send('clearlog 1\n')
                while not chan.recv_ready():
                    time.sleep(3)
                out = chan.recv(9999)
                if 'cleared' in out.decode("ascii"):
                    print('+ SUCCESS: Cleared SIP Log File for ' + str(ip) + '!')
                    sipCleared = True
                resultsDict['Phone Logs Cleared'] += 1

            ## SEND BYE IF NOT REBOOTING
            if not rebootStuck and not performActionsDict['do_reboot']:
                chan.send('bye\n') # send bye if not rebooting
            ## REBOOT 
            if performActionsDict['do_reboot'] or rebootStuck:
                chan.send('reboot\n')
                while not chan.recv_ready():
                    time.sleep(3)
                out = chan.recv(9999)
                if 'Rebooting!' in out.decode("ascii"):
                    print('+ SUCCESS: Rebooted ' + str(ip) + '!')
                    resultsDict['Phones Rebooted'] += 1
            print('## Completed Running Actions for ' + str(ip) + '!')
            success_hosts.append(ip)
            chan.close()  # Close Shell Channel
            client.close() # Close the client itself

            if window and performActionsDict['do_get_screen']:
                f_grab.write('------------------------------\n##### REPORT WINDOW DATA #####\n##### IP: ' + str(ip) + ' #####\n##### MAC: ' + phoneMAC + ' #####\n\n')
                f_grab.write(window.decode("ascii") + '\n\n')
            if genConfig and window:
                phoneNums = configFromScreenGrab(window, phoneMAC, ip)
                phoneInfoList[ip] = phoneInfoList[ip] + phoneNums
                resultsDict['Autologin Configs Generated'] += 1




# TRY EXCEPTIONS
        except paramiko.AuthenticationException:
            print('- Bad SSH Credentials: ' + str(ip))
            fail_hosts.append(ip)
            client.close()
        except paramiko.BadHostKeyException:
            print('- Bad Host Key: ' +str(ip))
            fail_hosts.append(ip)
            client.close()
        except paramiko.SSHException:
            print('- SSH Exception Error. Possible protocol issue: ' +str(ip))
            fail_hosts.append(ip)
            client.close()
        except:
            print('- Failed connecting to: ' + str(ip))
            client.close()
            fail_hosts.append(ip)

    # Close Window File
    if performActionsDict['do_get_screen']:
        f_grab.close()

   # Phone Info CSV
    if performActionsDict['do_generate_csv']:
        #print('inside IF LOOP for CSV')
        output_csv = 'phone-info-' + now.strftime('%Y-%m-%d-%H%M') + '.csv'
        outputpath = "output_files"
        makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.
        f = open(outputpath + '/' + output_csv, 'w')
        
        csvwriter = csv.writer(f)
        csvwriter.writerow(['IP', 'Model', 'Firmware', 'MAC', 'PhoneNum1','PhoneNum2','PhoneNum3','PhoneNum4','PhoneNum5','PhoneNum6'])
        for key in phoneInfoList.keys():
            data = [key]
            data = data + phoneInfoList[key]
            csvwriter.writerow(data)
            resultsDict['CSVs Generated'] += 1
        f.close()
        print('\n*****\nCSV Phone Info Output File Saved To: ' + outputpath + '/' + output_csv + '\n*****')
    #print('End of Action function')
    #print(performActionsDict)
    process_results('actions', resultsDict)

    

def configFromScreenGrab(screenGrab, MAC, ip):
    filename = "SIP" + MAC.upper() + ".cfg" # Set output filename
    outputpath = 'phone_configs'
    lineDict = defaultdict()
    file_logins = []
    maxlogins = 2
    file_contents = ['SLOW_START_200OK NO','ENABLE_LOCAL_ADMIN_UI NO','AUTO_UPDATE YES','AUTO_UPDATE_TIME 3600', 'AUTO_UPDATE_TIME_RANGE 3','AUTOLOGIN_ENABLE 2']
    phoneNums = []

    makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.

    for line in screenGrab.decode("ascii").splitlines():
        m = re.search("----\[([0-9][0-9][0-9][0-9]*)\] *, <LineKey#([1-8])", line)
        if m:
            lineDict[m.group(2)] = m.group(1)
    if lineDict:
        if len(lineDict) > 2:
            maxlogins = len(lineDict) # set max_login parameter to the number of phone numbers that will be auto-logged in.
        file_contents = file_contents + ['MAX_LOGINS '+ str(maxlogins)]
        orderedLineDict = OrderedDict(sorted(lineDict.items()))
        key = 1
        for k, v in orderedLineDict.items():  # Loop through each phone number in the list for the given MAC and create auto login.
            file_logins = file_logins + ['AUTOLOGIN_ID_KEY' + str(key).zfill(2) + ' '  + v + '@' + defaultDomain]
            file_logins = file_logins + ['AUTOLOGIN_PASSWD_KEY' + str(key).zfill(2) + ' ' + str(defaultPassword)]
            key += 1
            phoneNums.append(v)
        output = open(outputpath + '/' + filename, 'w') # Open Output file.
        output.write("\n\n".join(file_contents)) # Write static data in the file.
        output.write("\n\n")
        output.write("\n\n".join(file_logins)) # Write the auto login data
        results_file.write('+ SUCCESS: Writing File ' + filename + '\n')
        output.close() # Close the output file.
        print('+ SUCCESS: Writing File ' + filename)
        return phoneNums
    else:
        outputpath = 'phone_configs_nokeys'
        makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.

        print('- OOPS: No line keys detected for: ' + str(ip) + ' writing blank file to ' + outputpath)
        results_file.write('- OOPS: No line keys detected for: ' + str(ip) + ' writing blank file to ' + outputpath + '\n')
        key = 1
        file_contents = file_contents + ['MAX_LOGINS '+ str(maxlogins)]
        file_logins = file_logins + ['AUTOLOGIN_ID_KEY' + str(key).zfill(2) + ' ' + '0000000000@' + defaultDomain]
        file_logins = file_logins + ['AUTOLOGIN_PASSWD_KEY' + str(key).zfill(2) + ' ' + str(defaultPassword)]
        output = open(outputpath + '/' + filename, 'w') # Open Output file.
        output.write("\n\n".join(file_contents)) # Write static data in the file.
        output.write("\n\n")
        output.write("\n\n".join(file_logins)) # Write the auto login data
        results_file.write('+ SUCCESS: Writing File for BLANK PHONE NUMBER  ' + filename + '\n')
        output.close() # Close the output file.
        return phoneNums

def factory_reset_phone(Local_IPSet):
    clear()
    # WARNING PROMPT
    countIPs = len(Local_IPSet)
    clear_results()

    print('##### WARNING: YOU ARE ABOUT TO ATTEMPT TO FACTORY RESET ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return 0
    print('##### FINAL WARNING: ARE YOU SURE YOU WANT TO FACTORY RESET? #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return 0
    ## START LOOPING THROUGH ALL IP'S
    for ip in Local_IPSet:
        perform_factory_reset(ip)
    process_results('factory_reset')

def perform_factory_reset(ip):
    try:
        # Set up client and connect
        client = SSHClient()
        client.set_missing_host_key_policy(IgnorePolicy)
        
        client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

        # Open Shell on Client
        chan = client.invoke_shell()
        while not chan.recv_ready():
            time.sleep(1)
        out = chan.recv(9999)
        ## GET MAC ADDRESS
        m = re.search('.*MAC Address = (.*)\r\nIP', out.decode("ascii"))
        phonemac = m.group(1)
        ## FACTORY RESET 
        #print('+ Sending reset2factory to ' + str(ip))
        chan.send('reset2factory\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        if 'Reset to Default Settings... Are you sure?' in out.decode("ascii"):
            chan.send('Y\n') # Send Y confirmation
            while not chan.recv_ready():
                time.sleep(3)
            out = chan.recv(9999)
            if 'Enter MAC-address:' in out.decode("ascii"):
                #print('sending mac: ' + phonemac)
                chan.send(str(phonemac) + '\n') # Send MAC address for confirmation
                # while not chan.recv_ready():
                #     time.sleep(3)
                # out = chan.recv(9999)
                # if 'Incorrect MAC-address' in out.decode("ascii"):
                #     fail_hosts.append(ip)
                # else:
                print('Sending the Droids to Anchorhead...')
                time.sleep(10)
                print('+ SUCCESS: Factory Reset: ' + str(ip))
                success_hosts.append(ip)
            else:
                fail_hosts.append(ip)
                
        else:
            print('Error sending reset2factory command')
            fail_hosts.append(ip)
        #print('Closing Channel and SSH Client')
        chan.close()  # Close Shell Channel
        client.close() # Close the client itself
        #print('Closed. Done.')
    except paramiko.AuthenticationException:
        print('- Bad SSH Credentials: ' + str(ip))
        fail_hosts.append(ip)
        client.close()
        return -1
    except paramiko.BadHostKeyException:
        print('- Bad Host Key: ' +str(ip))
        fail_hosts.append(ip)
        client.close()
        return -1
    except paramiko.SSHException:
        print('- SSH Exception Error. Possible protocol issue: ' +str(ip))
        fail_hosts.append(ip)
        client.close()
        return -1
    except:
        print('- Failed connecting to: ' + str(ip))
        client.close()
        fail_hosts.append(ip)
        return -1
    return

def process_results(source, resultActionDict = False):
    if source == 'actions':
        task = 'Perform Actions'
    elif source == 'factory_reset':
        task = 'Factory Reset Phones'
    elif source == 'ping_ip':
        task = 'Ping All IPs'
    else:
        print('Error: Unknown Source Called Results Function.')
        time.sleep(1)
        input('Press Enter to Return to Menu')
        return
    print('\n### Summary of Results ###')
    print('# Task: ' + task)
    print('# Total Attempted: ' + str(len(IPSet)))
    print('# Successful: ' + str(len(success_hosts)))
    print('# Failures: ' + str(len(fail_hosts)))
    print('##########################')
    if resultActionDict:
        print('### Action Details ###')
        for key in resultActionDict:
            if resultActionDict[key] > 0:
                print('#', key, '--', str(resultActionDict[key]))
        print('##########################\n')
    results_file.write('Detailed Results for Task: ' + task + '\n')
    results_file.write('+++ SUCCESSFUL +++\n')
    for each in success_hosts:
        results_file.write(str(each) + '\n')
    results_file.write('--- FAILURES ---\n')
    for each in fail_hosts:
        results_file.write(str(each) + '\n')
    results_file.write('\n### Summary of Results ###\n')
    results_file.write('# Task: ' + task + '\n')
    results_file.write('# Total Attempted: ' + str(len(IPSet)) + '\n')
    results_file.write('# Successful: ' + str(len(success_hosts)) + '\n')
    results_file.write('# Failures: ' + str(len(fail_hosts)) + '\n')
    results_file.write('##########################\n')
    if resultActionDict:
        results_file.write('### Action Details ###\n')
        for key in resultActionDict:
            if resultActionDict[key] > 0:
                results_file.write('# ' + key + ' -- ' + str(resultActionDict[key]) + '\n')
        results_file.write('##########################\n\n')
    time.sleep(1)
    input('Press Enter to Return to Menu')
    clear()

def clear_results():
    global resultsDict
    global fail_hosts
    global success_hosts
    global numSuccess
    global numFail
    fail_hosts = []
    success_hosts = []
    numSuccess = 0
    numFail = 0
    resultsDict = {
    'Login Banners Acknowledged' : 0,
    'CSVs Generated' : 0,
    'Phone Screens Saved to File' : 0,
    'Autologin Configs Generated' : 0,
    'Phone Logs Cleared' : 0,
    'Phones Rebooted' : 0
    }

def cancel():
    print('\nCancelling...\n')
    time.sleep(1)
    clear()
    return

def printIPs(Local_IPSet):
    clear()
    if not customIPs:
        print('IP Addresses to be acted on from ' + inputfile + ':')
    else: 
        print('IP Addresses to be acted on from CUSTOM Range of ' + startIP + ' to ' + endIP)
    print(Local_IPSet)
    print('\n\n')
    time.sleep(1)
    input('Press Enter to Return to Menu')
    clear()

def pingIPs(Local_IPSet):
    global IPSet
    global customPingIPs
    clear()
    clear_results()
    countIPs = len(Local_IPSet)
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT TO PING ' + str(countIPs) + ' IP ADDRESSES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return
    outputpath = "output_files"
    now = datetime.datetime.now()
    pingresultsfile = 'ping-results-' + now.strftime('%Y-%m-%d-%H%M') + '.csv'
    makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.
    f = open(outputpath + '/' + pingresultsfile, 'w')
    csvwriter = csv.writer(f)
    csvwriter.writerow(['IP', 'Ping'])
    
    for ip in Local_IPSet:
        response = system("ping -c 1 -W 1 " + ip + " > /dev/null 2>&1")
        status = True
        if not response == 0:
            print('- Ping Failed to: ' + str(ip))
            status = False
            fail_hosts.append(ip)

        data = [str(ip),str(status)]
        if status == True:
            numSuccess =+ 1
            print('+ SUCCESS: Pinged ' + str(ip))
            success_hosts.append(ip)
        csvwriter.writerow(data)

    f.close()
    print('\n*****\nOutput File Saved To: ' + outputpath + '/' + pingresultsfile + '\n*****')
    process_results('ping_ip')

    # Prompt to set successful pings as new list
    proceed = input('Set the Successful Pings as New List? y/N: ')
    if proceed.upper() == 'Y':
        IPSet = success_hosts
        customPingIPs = True

def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')

def results_setup():
    global results_file_name
    global now
    global outputpath
    global results_file

    makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.
    results_file = open(outputpath + '/' + results_file_name, 'a')
    results_file.write('\n-----\n' + now.strftime('%Y-%m-%d %H:%M') + ' STARTING PDT TOOL\n')

def print_do_menu():
    countIPs = len(IPSet)
    performActionsDict = {
        'do_acknowledge_banner': False,
        'do_generate_csv': False,
        'do_get_screen': False,
        'do_generate_confg': False,
        'do_clear_logs': False,
        'do_reboot': False,
        'do_reboot_ifstuck': False
    }

    terminal_menu = TerminalMenu(
        ["Acknowledge Login Banner","Generate Phone Info CSV (IP, Model, MAC, FW Version)", "Get Phone Screen", "Generate Autologin Configs", "Clear Phone Logs", "Reboot Phone", "Reboot Phone if stuck logging in"],
        # Taking , "Reboot Phone if stuck logging in" out of list for now. May implement later.
        multi_select=True,
        show_multi_select_hint=True,
    )
    clear()
    print_menu_header()
    print('Choose actions to perform:')
    menu_entry_indices = terminal_menu.show()
    #print(menu_entry_indices)
    #print(terminal_menu.chosen_menu_entries)
    if not menu_entry_indices:
        return
    if 0 in menu_entry_indices:
        performActionsDict['do_acknowledge_banner'] = True
    if 1 in menu_entry_indices:
        performActionsDict['do_generate_csv'] = True
    if 2 in menu_entry_indices:
        performActionsDict['do_get_screen'] = True
    if 3 in menu_entry_indices:
        performActionsDict['do_generate_confg'] = True
    if 4 in menu_entry_indices:
        performActionsDict['do_clear_logs'] = True
    if 5 in menu_entry_indices:
        performActionsDict['do_reboot'] = True
    if 6 in menu_entry_indices:
        performActionsDict['do_reboot_ifstuck'] = True
    clear()
    print_menu_header()
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT THE FOLLOWING ACTIONS ON ' + str(countIPs) + ' PHONES #####')
    actions = []
    if performActionsDict['do_acknowledge_banner']:
        actions.append('* Acknowledge Login Banner')
    if performActionsDict['do_generate_csv']:
        actions.append('* Generate Phone Info CSV')
    if performActionsDict['do_get_screen']:
        actions.append('* Get Phone Screen Data')
    if performActionsDict['do_generate_confg']:
        actions.append('* Generate Autologin Configs')
    if performActionsDict['do_clear_logs']:
        actions.append('* Clear All Phone Logs')
    if performActionsDict['do_reboot']:
        actions.append('* Reboot Phone')
    if performActionsDict['do_reboot_ifstuck']:
        actions.append('* Reboot Phone if Stuck Logging In')
    for each in actions:
        print(each)
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return

    mainActions(IPSet, performActionsDict)

def start_pdt_tool():
    if not inputfile == 'None':
        usePing = 'n'
        file = open(inputfile,'r') # Open file in read only
        file_dict = csv.DictReader(file) # Read the CSV into a dictionary. Note: Header row of the CSV MUST contain MAC,Phone,

        ## Check for correct header row with IP field in the input file.
        if not 'IP' in file_dict.fieldnames:
            print('Error: ' + inputfile + ' does not contain a header row with "IP"\n')
            file.close() # Close the input file before erroring out.
            return
        ## Look for Ping Header
        if 'Ping' in file_dict.fieldnames:
            usePing = input('This file has Ping values. Only Use Successful Ping results? y/N: ')
            if usePing.upper() == 'Y':
                print('Importing only successfully pinged (True) IP addresses from file...')
                time.sleep(1)
            else:
                print('Importing ALL IP addresses from file...')
                time.sleep(1)


        ## Change CSV dict into a set of IP addresses.
        for row in file_dict:
            if usePing.upper() == 'Y':
                if row['Ping'] == 'True':  # Look for Ping True
                    try: # Adding IP validation to input file
                        netaddr.IPAddress(row['IP'])
                        IPSet.add(row['IP']) # Only add IP if Ping was True in the file
                    except:
                        print(str(row['IP']) + ' is Not a Valid IP Address')
                        time.sleep(2)
            else:
                try: # Adding IP validation to input file
                    netaddr.IPAddress(row['IP'])
                    IPSet.add(row['IP']) # Only add IP if Ping was True in the file
                except:
                    print(str(row['IP']) + ' is Not a Valid IP Address')
                    time.sleep(2)

    results_setup()

    while(True):
        clear()
        print_menu()
        option = ''
        try:
            print('\n')
            option = int(input('Enter your choice: '))
        except:
            print('Wrong input. Please enter a number ...')
        #Check what choice was entered and act accordingly
        if option == 1:
            set_ssh_creds()
            input('Press Enter to return to the menu.')
            print('\n\n')
        elif option == 2:
            set_ip_range()
        elif option == 3:
            printIPs(IPSet)
        elif option == 4:
            pingIPs(IPSet)
        elif option == 5:
            print_do_menu()
        elif option == 6:
            factory_reset_phone(IPSet)
        elif option == 0:
            if not inputfile == 'None':
                file.close()
            results_file.close()
            print('\nThank you! Come again!')
            time.sleep(1)
            clear()
            exit()
        else:
            print('\n***Invalid option. Please enter a number between 1 and 6 or 0 to Exit.\n')
            time.sleep(2)

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Input CSV File')
    parser.add_argument("-f", "--file", required=False, help='Filename or path to CSV input file containing phone IP addresses.')
    args = parser.parse_args()
    inputfile = str(args.file)

    start_pdt_tool()