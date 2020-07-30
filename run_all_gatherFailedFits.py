import os, sys, json
import pandas as pd
from ROOT import *
from subprocess import call

print "Usage: python gatherFailedFits.py datacard_folder"

current_dir = os.getcwd()
datacard_path = sys.argv[1]

signal_folders = [folder for folder in os.listdir(datacard_path) if os.path.isdir(os.path.join(datacard_path, folder))]
if not signal_folders:
    print "Found no signal directory inside %s"%datacard_path
for signal_folder in signal_folders:
    out_str = ''
    out_str_exp = ''
    os.chdir(os.path.join(datacard_path, signal_folder))
    nll_files = [nll_file for nll_file in os.listdir(".") if nll_file.endswith('nll.root')]
    if not nll_files:
        print "Found no nll root files in directory %s"%os.path.join(datacard_path, signal_folder)
    for nll_file in nll_files:
        try:
            impact_json = nll_file.replace('_nll.root', '_impacts.json')
            impact_json_exp = nll_file.replace('_nll.root', '_expected_impacts.json')

            if os.path.isfile(nll_file) and os.path.isfile(impact_json_exp):
                print "Comparing " + nll_file + " and " + impact_json_exp
                out_str_exp += "Comparing " + nll_file + " and " + impact_json_exp + '\n'
            else:
                print "One of file missing in " + nll_file.replace('_nll.root', '')
                out_str_exp += "One of file missing in " + nll_file.replace('_nll.root', '') + '\n'
            if os.path.isfile(nll_file) and os.path.isfile(impact_json):
                print "Comparing " + nll_file + " and " + impact_json
                out_str += "Comparing " + nll_file + " and " + impact_json + '\n'
            else:
                print "One of file missing in " + nll_file.replace('_nll.root', '')
                out_str += "One of file missing in " + nll_file.replace('_nll.root', '') + '\n'

            f_nll = TFile.Open(nll_file, 'READ')
            nll_list = [l.GetName() for l in f_nll.GetListOfKeys() if not any(der in l.GetName() for der in ['_d1', '_d2'])]
            nll_list.remove('r')

            with open(impact_json_exp) as jsonfile_exp:
                data = json.load(jsonfile_exp)
            df_exp = pd.DataFrame.from_dict(data['params'], orient='columns')
            impact_list_exp = [str(row) for row in df_exp['name']]

            filtered_exp = [i for i in nll_list if not i in impact_list_exp]
            out_str_exp += str(filtered_exp) + '\n'

            with open(impact_json) as jsonfile:
                data = json.load(jsonfile)
            df = pd.DataFrame.from_dict(data['params'], orient='columns')
            impact_list = [str(row) for row in df['name']]

            filtered = [i for i in nll_list if not i in impact_list]
            out_str += str(filtered) + '\n'
        except: pass

    out_name_exp = 'FCNC_' + signal_folder + '_Discriminant_DNN_' + signal_folder + '_Impact_expected_MultiDimFit_Failed.txt'
    out_file_exp =  open(out_name_exp ,'w')
    print>>out_file_exp, out_str_exp

    out_name = 'FCNC_' + signal_folder + '_Discriminant_DNN_' + signal_folder + '_Impact_MultiDimFit_Failed.txt'
    out_file =  open(out_name ,'w')
    print>>out_file, out_str

    os.chdir(current_dir)
