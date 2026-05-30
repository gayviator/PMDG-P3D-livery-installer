# Credits for function to invoke PS script
# Source - https://stackoverflow.com/a/78647253
# Posted by Nirav Mistry
# Retrieved 2026-05-27, License - CC BY-SA 4.0
#
# PowerShell script by Wintermute
#
# IMPORTANT NOTES
# only supports packages with one texture folder
# does not work uncompiled (as .py)
# does not work when called through relative path in cmd
# best results with PTP files in same folder as EXE

import configparser
import os
import subprocess
import shutil
from pathlib import Path
from winreg import *

# Function to run unpack.ps1
def pscript(script_path, *params):

    commandline_options = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', script_path]
    for param in params:
        commandline_options.append(param)

    process_result = subprocess.run(commandline_options, stdout = subprocess.PIPE, stderr = subprocess.PIPE, universal_newlines = True)

    ##print(process_result.returncode)  # PRINT RETURN CODE OF PROCESS  0 = SUCCESS, NON-ZERO = FAIL  
    print(process_result.stdout)      # PRINT STANDARD OUTPUT FROM POWERSHELL
    print(process_result.stderr)      # PRINT STANDARD ERROR FROM POWERSHELL ( IF ANY OTHERWISE ITS NULL|NONE )

    if process_result.returncode == 0:
        Message = 'Success !'
    else:
        Message = 'Error Occurred !'

    return Message



# Get list of PTPs opened with EXE (does not work uncompiled)
ptp_list = sys.argv
# Set script path, cwd from first argument (does not work when launched through rel path in cmd)
os.chdir(sys.argv[0].replace('\\PMDG Livery Installer.exe', ''))



print('=================\nPMDG Livery Installer\nfor Prepar3D v1-5\n=================')



# Ask for PTP path if no file was used
if len(ptp_list) <= 1:
    cont = True
    while cont:
        ptp_list.append(input('Please type the FULL path to the PTP file(s) you want to install.\nPlease read the README for proper use of this program\nPath goes here: ').replace("'", '').replace('"', '').replace('.ptp', '')+'.ptp')
        cont = input('Would you like to add another file? (y/n): ').lower() == 'y'

# Delete script path from arguments list
del ptp_list[0]

for ptp_path in ptp_list:

    # Unpack PTP
    print('Unpacking', ptp_path, '...\n(Expect a large log from the unpacker)')
    out_path = Path(ptp_path.replace('.ptp', '').replace('+', ' '))
    print(pscript(os.path.join(os.getcwd(),'_internal\\unpack.ps1'), ptp_path))
    
    # Find texture folder in output (currently only picks last folder, error if multiple)
    out_list = os.listdir(out_path)
    tex_counter = 0
    for x in out_list:
        if x.lower().startswith('texture.'):
            tex_folder = x
            tex_counter += 1
    if tex_counter > 1:
        print('Multiple textures found in "', ptp_path+'". Please install manually.')
        continue
    
    # Ask to isntall
    tis_the_question = input(ptp_path+' has been unpacked.\nWould you like me to try to install this livery for you? (y/n): ')
    if not tis_the_question.lower() == 'y':
        continue
            
    # Read P3D install path from registry
    p3dversion = input('Which version of P3D do you wish to install "'+ptp_path+'" to?\n(Number only, e.g. enter "5" for P3Dv5), leave empty to skip this livery: ')
    if not p3dversion in ['1', '2', '3', '4', '5', '6']:
        print('Invalid P3D version, skipping this livery...\n\n\n')
        continue
    p3dpath = Path(QueryValueEx(OpenKey(ConnectRegistry(None, HKEY_CURRENT_USER), 'SOFTWARE\\Lockheed Martin\\Prepar3D v'+p3dversion),'AppPath')[0])
    print('Prepar3D installation found at', str(p3dpath))
    
    # Read Settings.dat for product/variant, Config.cfg for registration and entry, set SimObject directory
    config_dat = configparser.RawConfigParser()
    config_dat.read(os.path.join(out_path, 'Settings.dat'))
    ac_prod = config_dat['Settings']['Aircraft']
    ac_var = config_dat['Settings']['Variant']
    config_cfg = configparser.RawConfigParser(inline_comment_prefixes=('#', ';', '//'))
    config_cfg.read(os.path.join(out_path, 'Config.cfg'))
    ac_reg = config_cfg['fltsim.x']['atc_id']
    print('Detected product', ac_prod, 'variant', ac_var, 'registration', ac_reg)
    simobject = os.path.join(p3dpath, 'SimObjects\\Airplanes', ac_var)
    
    # Automatic product selection, dictionary {'aircraft name in settings.dat': 'aircraft folder name in Prepar3D v5\PMDG']
    products = {'PMDG 747-400 V3': 'PMDG 747 QOTS II',
                'PMDG 737NGXu': 'PMDG 737 NGXu',
                'PMDG 777X': 'PMDG 777X',
                'PMDG DC-6': 'PMDG DC-6',
                'PMDG 737NGX': 'PMDG 737 NGX'}
    work = os.path.join(p3dpath, 'PMDG\\'+products[ac_prod]+'\\Aircraft')

    # Parse, checkaircraft.cfg for desired variant
    ac_cfg_path = os.path.join(simobject, 'aircraft.cfg')
    ac_cfg = configparser.RawConfigParser(inline_comment_prefixes=('#', ';', '//'))
    ac_cfg.read(ac_cfg_path)
    if not 'fltsim.0' in ac_cfg:
        print('Invalid or missing aircraft.cfg for', ac_var+', skipping this livery...\n\n\n.')
        continue
    
    # Copy Aircraft.ini
    try:
        shutil.copy(os.path.join(out_path, 'Aircraft.ini'), os.path.join(work, ac_reg+'.ini'))
    except FileNotFoundError:
        print('Specific aircraft configuration not found.')
    except Exception as error:
        print('Couldn\'t copy Aircraft.ini configuration file:', type(error).__name__)
    else:
        print(ac_reg+'.ini configuration file copied successfully')
        
    # Back up aircraft.cfg
    try:
        shutil.copy(ac_cfg_path, ac_cfg_path.replace('.cfg', '.cfg.bak'))
    except FileExistsError:
        print('Aircraft.cfg backup file already exists for', ac_var)
    except FileNotFoundError:
        print('Config.cfg or Aircraft.cfg file not found for', ac_var)
    except:
        print('Couldn\'t back up Aircraft.cfg file, skipping this livery...\n\n\n')
    
    # Copy textures
    try:
        shutil.copytree(os.path.join(out_path, tex_folder), os.path.join(simobject, tex_folder))
    except FileNotFoundError:
        print('The livery\'s texture folder was not found')
    except FileExistsError:
        print('Texture folder for', ac_var, '"', tex_folder, '" already exists')
    except Exception as error:
        print('Couldn\'t copy texture files from "', tex_folder, '" for', ac_var, ';', type(error).__name__, '\nPlease copy these manually from the output folder.')
    else:
        print('Texture files for', ac_var, 'copied successfully')

    # Add aircraft.cfg entry
    final_cfg = open(ac_cfg_path, 'w')
    backup_cfg = open(ac_cfg_path.replace('.cfg', '.cfg.bak'), 'r')
    config_cfg_plain = open(os.path.join(out_path, 'Config.cfg'), 'r')
    
    for line in backup_cfg:
        if 'fltsim.' in line:
            next_fltsim_idx = int(list(line)[8]) + 1
        if '[General]'.lower() in line.lower():
            print('Adding entry fltsim.'+str(next_fltsim_idx))
            for entry_line in config_cfg_plain:
                final_cfg.write(entry_line.replace('fltsim.x','fltsim.'+str(next_fltsim_idx)))
            final_cfg.write('\n')
        final_cfg.write(line)

    backup_cfg.close()
    config_cfg_plain.close()
    final_cfg.close()

    print('\nInstallation complete. Recommended to check logs and files.\n')

print('A copy of the unpacked files for each livery can be found in the same directory as the original PTP file. Happy flying!\n')
os.system('pause')

