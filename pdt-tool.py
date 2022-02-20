################### AVAYA 1100 SERIES PDT TOOL ######################
## Python tool to easily integrate with an Avaya 1100 series PDT menu via SSH.
## Input CSV with at least columns: IP
## 
## Requires Python 3. For older linux versions with both, use "python3" to initiate script.
##
## USAGE: python3 pdt-tool.py [csv input file]
## EXAMPLE: python3 pdt-tool.py sample-csv.csv
## 
## Version: 1.0.0
## Updated: 2022-02-19
## Author: Brett Barker - brett.barker@brbtechsolutions.com 
########################################BRB####################################################


from paramiko import AutoAddPolicy, SSHClient
import time
import csv
import datetime
import sys
import re
import datetime
import os

#GLOBAL VARIABLES
SSH_Username = 'help'   # Default value if not changed in user prompt.
SSH_Pass = '1234'       # Default value if not changed in user prompt.
inputfile = ''
success_hosts = []
fail_hosts = []
IPSet = set()

menu_options = {
    1: 'Set SSH User/Pass',
    2: 'Get Model, Mac, FW version',
    3: 'Reboot Phones',
    4: 'Clear All Phone Logs',
    5: 'Factory Reset Phones',
    6: 'Exit',
}

def print_menu():
    print('----------------------------------------------------')
    print('Welcome to the unofficial Avaya 1100 Series PDT Tool')
    print('----------------------------------------------------')
    print('     SSH User: ' + SSH_Username + '   SSH Password: ' + SSH_Pass)
    print('     Input File: ' + inputfile)
    print('     Total IPs in File: ' + str(len(IPSet)))
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

def option2():
     os.system('clear')
     print('\nThis feature is coming soon.')
     time.sleep(3)
     os.system('clear')

def reboot_phones(IPSet):
    clear_results()
    countIPs = len(IPSet)
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT TO REBOOT ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        print('\nCancelling...\n')
        time.sleep(2)
        return
    for ip in IPSet:
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
        else:
            fail_hosts.append(ip)
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
    return    
    
def clear_phone_logs(IPSet):
    clear_results()
    countIPs = len(IPSet)
    print('##### INFO: YOU ARE ABOUT TO ATTEMPT TO CLEAR LOGS ON ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        print('\nCancelling...\n')
        time.sleep(2)
        return
    for ip in IPSet:
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
        ## CLEAR LOG 0
        chan.send('clearlog 0\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        ## CLEAR LOG 1
        chan.send('clearlog 1\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        #print(out.decode("ascii"))
        if 'cleared' in out.decode("ascii"):
            print('+ Successfully cleared logs for ' + str(ip) + '!')
            success_hosts.append(ip)
        else:
            fail_hosts.append(ip)
        chan.send('bye\n')
        while not chan.recv_ready():
            time.sleep(3)
        out = chan.recv(9999)
        
    except:
        print('- Failed connecting to: ' + str(ip))
        fail_hosts.append(ip)
    return

def factory_reset_phone(IPSet):
    # WARNING PROMPT
    countIPs = len(IPSet)
    clear_results()

    print('##### WARNING: YOU ARE ABOUT TO ATTEMPT TO FACTORY RESET ' + str(countIPs) + ' PHONES #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        print('Cancelling...')
        return 0
    print('##### FINAL WARNING: ARE YOU SURE YOU WANT TO FACTORY RESET? #####')
    proceed = input('PROCEED? y/N: ')
    if not proceed.upper() == 'Y':
        print('Cancelling...')
        return 0
    ## START LOOPING THROUGH ALL IP'S
    for ip in IPSet:
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
    else:
        print('Error: Unknown Source Called Results Function.')
        return
    print('\n### Summary of Results ###')
    print('# Task: ' + task)
    print('# Successful: ' + str(len(success_hosts)))
    print('# Failures: ' + str(len(fail_hosts)))
    print('##########################\n')
    time.sleep(1)
    input('Press Enter to Return to Menu')
    os.system('clear')

def clear_results():
    global fail_hosts
    global success_hosts
    fail_hosts = []
    success_hosts = []


def start_pdt_tool():
    
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

    while(True):
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
            option2()
        elif option == 3:
            reboot_phones(sorted(IPSet))
        elif option == 4:
            clear_phone_logs(sorted(IPSet))
        elif option == 5:
            factory_reset_phone(sorted(IPSet))
        elif option == 6:
            print('Thank you! Come again!')
            exit()
        else:
            print('\n***Invalid option. Please enter a number between 1 and 4.\n')

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Input CSV File')
    parser.add_argument("-f", "--file", required=True, help='Filename or path to CSV input file containing phone IP addresses.')
    args = parser.parse_args()
    inputfile = str(args.file)

    start_pdt_tool()
