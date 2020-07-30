import os, sys
from subprocess import call

print "Usage: python run_all_limits.py datacard_folder"

current_dir = os.getcwd()
datacard_path = sys.argv[1]

signal_folders = [folder for folder in os.listdir(datacard_path) if os.path.isdir(os.path.join(datacard_path, folder))]
if not signal_folders:
    print "Found no signal directory inside %s"%datacard_path
for signal_folder in signal_folders:
    os.chdir(os.path.join(datacard_path, signal_folder))
    limit_scripts = [limit_script for limit_script in os.listdir(".") if limit_script.endswith('run_limits.sh')]
    if not limit_scripts:
        print "Found no limit script in directory %s"%os.path.join(datacard_path, signal_folder)
    for limit_script in limit_scripts:
        if 'fullComb' in datacard_path and not 'all' in limit_script: continue
        print "Executing %s"%limit_script
        call(['bash', limit_script])
    os.chdir(current_dir)
