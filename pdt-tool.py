################### AVAYA 1100 SERIES PDT TOOL ######################
## Python tool to easily integrate with an Avaya 1100 series PDT menu via SSH.
## Input CSV with at least columns: IP
## 
## Requires Python 3. For older linux versions with both, use "python3" to initiate script.
##
## USAGE: python3 pdt-tool.py [csv input file]
## EXAMPLE: python3 pdt-tool.py sample-csv.csv
## 
## Version: 1.3.2
## Updated: 2022-02-24
## Author: Brett Barker - brett.barker@brbtechsolutions.com 
########################################BRB####################################################


from paramiko import AutoAddPolicy, SSHClient
import time
import csv
import datetime
import re
import datetime
from os import system, name, makedirs
from pathlib import Path
from collections import defaultdict
import netaddr



#GLOBAL VARIABLES
SSH_Username = 'help'   # Default value if not changed in user prompt. Can be modified here.
SSH_Pass = '1234'       # Default value if not changed in user prompt. Can be modified here.
inputfile = ''
success_hosts = []
fail_hosts = []
IPSet = set()
now = datetime.datetime.now()
output_csv = 'phone-info-' + now.strftime('%Y-%m-%d-%H%M') + '.csv'
results_file_name = 'pdt-tool-' + now.strftime('%Y-%m-%d-%H%M') + '.log'
outputpath = "pdt-tool-logs"
results_file = ''
startIP = ''
endIP = ''
customIPs = False


menu_options = {
    1: 'Set SSH User/Pass',
    2: 'Set Custom IP Range',
    3: 'List IP Addresses',
    4: 'Get Model, Mac, FW version',
    5: 'Reboot Phones',
    6: 'Clear All Phone Logs',
    7: 'Factory Reset Phones',
    8: 'Exit',
}

def print_menu():
    print('----------------------------------------------------')
    print('Welcome to the unofficial Avaya 1100 Series PDT Tool')
    print('----------------------------------------------------')
    print('     SSH User: ' + SSH_Username + '   SSH Password: ' + SSH_Pass)
    if not customIPs:
        print('     Input File: ' + inputfile)
        print('     Total IPs in File: ' + str(len(IPSet)))
    else:
        print('     CUSTOM IP RANGE: ' + str(startIP) + ' to ' + str(endIP))
        print('     Total IPs in Range: ' + str(len(IPSet)))
    print('     Log File: ' + outputpath + '/' + results_file_name)
    print('----------------------------------------------------')
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

def getPhoneInfo(Local_IPSet):
    clear()
    clear_results()
    countIPs = len(Local_IPSet)
    phoneInfoList = defaultdict(list)
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT TO GET INFO FROM ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return
    for ip in Local_IPSet:
        r1 = perform_get_info(ip)
        if not r1 == -1:
            phoneInfoList[str(ip)].extend(r1)
        #print(phoneInfoList[ip])

    
    # Write to CSV
    outputpath = "output_files"
    makedirs(outputpath, exist_ok = True) # Make output directory if it doesn't exist.
    f = open(outputpath + '/' + output_csv, 'w')
    
    csvwriter = csv.writer(f)
    csvwriter.writerow(['IP', 'Model', 'Firmware', 'MAC'])
    for key in phoneInfoList.keys():
        data = [key]
        data = data + phoneInfoList[key]
        csvwriter.writerow(data)
    f.close()
    print('\n*****\nOutput File Saved To: ' + outputpath + '/' + output_csv + '\n*****')
    process_results('get_info')

def perform_get_info(ip):
    try:
        # Set up client and connect
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy)
        client.load_host_keys('known_phones')
        client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

        # Open Shell on Client
        chan = client.invoke_shell()
        out = chan.recv(9999)
        ## GET Phone Info
        m = re.search('.*connected to (.*). \r\r\nHW ID     :.*\r\nRAM size  :.*\r\nHW version.*\r\nFW version: (.*)\r\nMAC Address = (.*)\r\nIP', out.decode("ascii"))
        phoneModel = m.group(1)
        phoneFirmware = m.group(2)
        phoneMAC = m.group(3)
        #print(phoneModel + phoneFirmware + phoneMAC)
        chan.send('bye\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        print('+ Successfully got info for ' + str(ip) + '!')
        success_hosts.append(ip)
        chan.close()  # Close Shell Channel
        client.close() # Close the client itself
        return phoneModel, phoneFirmware, phoneMAC
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
        return -1

def reboot_phones(Local_IPSet):
    clear()
    clear_results()
    countIPs = len(Local_IPSet)
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT TO REBOOT ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return
    for ip in Local_IPSet:
        perform_reboot(ip)

    process_results('reboot_phones')

def perform_reboot(ip):
    try:
        # Set up client and connect
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy)
        client.load_host_keys('known_phones')
        client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

        # Open Shell on Client
        #print('-----Invoking shell')
        chan = client.invoke_shell()
        out = chan.recv(9999)
        ## REBOOT 
        chan.send('reboot\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        if 'Rebooting!' in out.decode("ascii"):
            print('+ Successfully rebooted ' + str(ip) + '!')
            success_hosts.append(ip)
            chan.close()  # Close Shell Channel
            client.close() # Close the client itself
        else:
            fail_hosts.append(ip)
            chan.close()  # Close Shell Channel
            client.close() # Close the client itself
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
    return    
    
def clear_phone_logs(Local_IPSet):
    clear()
    clear_results()
    countIPs = len(Local_IPSet)
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT TO CLEAR LOGS ON ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        cancel()
        return
    for ip in Local_IPSet:
        perform_log_clear(ip)

    process_results('clear_logs')


def perform_log_clear(ip):
    try:
        # Set up client and connect
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy)
        client.load_host_keys('known_phones')
        client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

        # Open Shell on Client
        #print('-----Invoking shell')
        chan = client.invoke_shell()
        out = chan.recv(9999)
        ecrCleared = False
        sipCleared = False
        ## CLEAR LOG 0
        chan.send('clearlog 0\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        if 'cleared' in out.decode("ascii"):
            print('+ Successfully cleared ECR Log File for ' + str(ip) + '!')
            ecrCleared = True
        ## CLEAR LOG 1
        chan.send('clearlog 1\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        #print(out.decode("ascii"))
        if 'cleared' in out.decode("ascii"):
            print('+ Successfully cleared SIP Log File for ' + str(ip) + '!')
            sipCleared = True
        if ecrCleared and sipCleared:
            success_hosts.append(ip)
        else:
            fail_hosts.append(ip)
        chan.send('bye\n')
        #while not chan.recv_ready():  # Shouldn't need to listen for data after the bye
        #    time.sleep(3)
        #out = chan.recv(9999)
        chan.close()  # Close Shell Channel
        client.close() # Close the client itself
        
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
    return

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
        client.set_missing_host_key_policy(AutoAddPolicy)
        client.load_host_keys('known_phones')
        client.connect(ip, username=SSH_Username, password=SSH_Pass, look_for_keys=False, allow_agent=False, banner_timeout=3, timeout=3)

        # Open Shell on Client
        chan = client.invoke_shell()
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
                chan.send(str(phonemac) + '\n') # Send MAC address for confirmation
                while not chan.recv_ready():
                    time.sleep(3)
                out = chan.recv(9999)
                if 'Incorrect MAC-address' in out.decode("ascii"):
                    fail_hosts.append(ip)
                else:
                    print('+ Successfully factory reset: ' + str(ip))
                    success_hosts.append(ip)
            else:
                fail_hosts.append(ip)
                
        else:
            print('Error sending reset2factory command')
            fail_hosts.append(ip)

        chan.close()  # Close Shell Channel
        client.close() # Close the client itself
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
    return

def process_results(source):
    if source == 'reboot_phones':
        task = 'Reboot Phones'
    elif source == 'clear_logs':
        task = 'Clear Phone Logs'
    elif source == 'factory_reset':
        task = 'Factory Reset Phones'
    elif source =='get_info':
        task = 'Get Phone Info'
    else:
        print('Error: Unknown Source Called Results Function.')
        return
    print('\n### Summary of Results ###')
    print('# Task: ' + task)
    print('# Total Attempted: ' + str(len(IPSet)))
    print('# Successful: ' + str(len(success_hosts)))
    print('# Failures: ' + str(len(fail_hosts)))
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
    results_file.write('##########################\n\n')
    time.sleep(1)
    input('Press Enter to Return to Menu')
    clear()

def clear_results():
    global fail_hosts
    global success_hosts
    fail_hosts = []
    success_hosts = []

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

def clear():
    # for windows
    if name == 'nt':
        _ = system('cls')
 
     # for mac and linux(here, os.name is 'posix')
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


def start_pdt_tool():
    if not inputfile == 'None':
        file = open(inputfile,'r') # Open file in read only
        file_dict = csv.DictReader(file) # Read the CSV into a dictionary. Note: Header row of the CSV MUST contain MAC,Phone,

        ## Check for correct header row with IP field in the input file.
        if not 'IP' in file_dict.fieldnames:
            print('Error: ' + inputfile + ' does not contain a header row with "IP"\n')
            file.close() # Close the input file before erroring out.
            return
        ## Change CSV dict into a set of IP addresses.
        for row in file_dict:
            IPSet.add(row['IP']) # Add IP to set
    Path('known_phones').touch()

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
            printIPs(sorted(IPSet))
        elif option == 4:
            getPhoneInfo(sorted(IPSet))
        elif option == 5:
            reboot_phones(sorted(IPSet))
        elif option == 6:
            clear_phone_logs(sorted(IPSet))
        elif option == 7:
            factory_reset_phone(sorted(IPSet))
        elif option == 8:
            if not inputfile == 'None':
                file.close()
            results_file.close()
            print('\nThank you! Come again!')
            time.sleep(1)
            clear()
            exit()
        else:
            print('\n***Invalid option. Please enter a number between 1 and 8.\n')

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Input CSV File')
    parser.add_argument("-f", "--file", required=False, help='Filename or path to CSV input file containing phone IP addresses.')
    args = parser.parse_args()
    inputfile = str(args.file)

    start_pdt_tool()
