#! /bin/env python

# Python imports
import os, sys, stat, argparse, getpass, json
from math import sqrt
from collections import OrderedDict
from subprocess import check_call

# to prevent pyroot to hijack argparse we need to go around
tmpargv = sys.argv[:] 
sys.argv = []

# ROOT imports
import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True
sys.argv = tmpargv

cmssw_base = os.environ['CMSSW_BASE']

parser = argparse.ArgumentParser(description='Create shape datacards ready for combine')

parser.add_argument('-p16', '--path16', action='store', dest='path_16', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/datacards_200101_2016v8', help='Directory containing data cards of 2016 analysis')
parser.add_argument('-p17', '--path17', action='store', dest='path_17', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/datacards_200101_2017v8', help='Directory containing data cards of 2017 analysis')
parser.add_argument('-p18', '--path18', action='store', dest='path_18', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/datacards_200101_2018v8', help='Directory containing data cards of 2018 analysis')
parser.add_argument('-o', '--output', action='store', dest='output', type=str, default='fullComb_default', help='Output directory, please follow convention to distunguish input cards') 
parser.add_argument('--nosys', action='store', dest='nosys', default=False, help='Consider or not systematic uncertainties (NB : bbb uncertainty is with another flag)')

options = parser.parse_args()

jetcats = ['b2j3','b2j4','b3j3','b3j4','b4j4','all']
years = ['1617','1718','161718']

if cmssw_base not in options.path_16:
  options.path_16 = os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', options.path_16)
if cmssw_base not in options.path_17:
  options.path_17 = os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', options.path_17)
if cmssw_base not in options.path_18:
  options.path_18 = os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', options.path_18)
if cmssw_base not in options.output:
  options.output = os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', options.output)

try:
  os.makedirs( options.output )
  os.makedirs( os.path.join(options.output, 'Hut') )
  os.makedirs( os.path.join(options.output, 'Hct') )
except:
  print "Limit folder already exist! Overwriting contents"
  pass

# Firstly, deal with partial correlation
# Write here: 'source1,corr1:source2,corr2:...'
partCorr_dict = {'16':'CMS_lumi,0.2',
                 '17':'CMS_lumi,0.3',
                 '18':'CMS_lumi,0.3'
}

for each_year in ['16','17','18']:
  for signal in ['Hct', 'Hut']:
    if   each_year == '16': datacard_dir = options.path_16
    elif each_year == '17': datacard_dir = options.path_17
    elif each_year == '18': datacard_dir = options.path_18

    os.chdir( os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', datacard_dir, signal) )

    for jetcat in jetcats:
      card_name = 'FCNC_{}_Discriminant_DNN_{}_{}.dat'.format(signal, signal, jetcat)
      output_name = 'forCombine_FCNC_{}_Discriminant_DNN_{}_{}'.format(signal, signal, jetcat)

      check_call('partialCorrelationEdit.py {} -m 125 --process {} --postfix-uncorr _20{} --output-txt {}.dat --output-root {}.root'
                 .format(card_name, partCorr_dict[each_year], each_year, output_name, output_name), shell=True)


for signal in ['Hct', 'Hut']:
  os.chdir( os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', options.output, signal) )
  output_prefix_list = []

  for jetcat in jetcats:
    for year in years:
      #card_name = 'FCNC_{}_Discriminant_DNN_{}_{}.dat'.format(signal, signal, jetcat)
      card_name = 'forCombine_FCNC_{}_Discriminant_DNN_{}_{}.dat'.format(signal, signal, jetcat)
      command_string = 'combineCards.py'
      if '16' in year: command_string += ' year_2016=' + os.path.join(options.path_16, signal, card_name)
      if '17' in year: command_string += ' year_2017=' + os.path.join(options.path_17, signal, card_name)
      if '18' in year: command_string += ' year_2018=' + os.path.join(options.path_18, signal, card_name)
      command_string += ' > FCNC_{}_Discriminant_DNN_{}_{}_{}.dat'.format(signal, signal, year, jetcat)
      check_call(command_string, shell=True)
      output_prefix_list.append('FCNC_{}_Discriminant_DNN_{}_{}_{}'.format(signal, signal, year, jetcat))


      # Backgrounds is a list of string of the considered backgrounds corresponding to entries in processes_mapping
      # Signals is a list of string of the considered signals corresponding to entries in processes_mapping
      # discriminant is the corresponding entry in the dictionary discriminants

  fake_mass = '125'

  # Write card
  for output_prefix in output_prefix_list:
    output_dir = os.path.join(options.output, signal)
    datacard = os.path.join(output_dir, output_prefix + '.dat')
    workspace_file = os.path.basename( os.path.join(output_dir, output_prefix + '_combine_workspace.root') )
    script = """#! /bin/bash

text2workspace.py {datacard} -m {fake_mass} -o {workspace_root}

# Run limit

echo combine -M AsymptoticLimits -n {name} {workspace_root} -S {systematics} --run expected #-v +2
combine -M AsymptoticLimits -n {name} {workspace_root} -S {systematics} --run expected #-v +2
#combine -H AsymptoticLimits -M HybridNew -n {name} {workspace_root} -S {systematics} --LHCmode LHC-limits --expectedFromGrid 0.5 #for ecpected, use 0.84 and 0.16
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
    script_file = os.path.join(output_dir, output_prefix + '_run_limits.sh')
    with open(script_file, 'w') as f:
        f.write(script)
    
    st = os.stat(script_file)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

    # Write small script for datacard checks
    script = """#! /bin/bash

# Run checks
echo combine -M FitDiagnostics -t -1 --expectSignal 0 {datacard} -n fitDiagnostics_{name}_bkgOnly -m 125 --robustHesse 1 --robustFit=1 --rMin -20 --rMax 20 #--plots
echo python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgOnly.root -g fitDiagnostics_{name}_bkgOnly_plots.root
combine -M FitDiagnostics -t -1 --expectSignal 0 {datacard} -n _{name}_bkgOnly -m 125 --robustHesse 1 --robustFit=1 --rMin -20 --rMax 20 #--plots
python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgOnly.root -g fitDiagnostics_{name}_bkgOnly_plots.root > fitDiagnostics_{name}_bkgOnly.log
python ../../printPulls.py fitDiagnostics_{name}_bkgOnly_plots.root
combine -M FitDiagnostics -t -1 --expectSignal 1 {datacard} -n _{name}_bkgPlusSig -m 125 --robustHesse 1 --robustFit=1 --rMin -20 --rMax 20 #--plots
python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgPlusSig.root -g fitDiagnostics_{name}_bkgPlusSig_plots.root > fitDiagnostics_{name}_bkgPlusSig.log
python ../../printPulls.py fitDiagnostics_{name}_bkgPlusSig_plots.root

#print NLL for check
combineTool.py -M FastScan -w {name}_combine_workspace.root:w -o {name}_nll
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
    script_file = os.path.join(output_dir, output_prefix + '_run_closureChecks.sh')
    with open(script_file, 'w') as f:
        f.write(script)
    
    st = os.stat(script_file)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

    # Write small script for impacts
    script = """#! /bin/bash

## Run impacts
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --doInitialFit --robustFit=1 --robustHesse 1 --rMin -20 --rMax 20 -t -1
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --robustFit=1 --robustHesse 1 --doFits --rMin -20 --rMax 20 -t -1 --parallel 32
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 -o {name}_expected_impacts.json --rMin -20 --rMax 20 -t -1
plotImpacts.py -i {name}_expected_impacts.json -o {name}_expected_impacts --per-page 40

combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --doInitialFit --robustFit=1 --robustHesse 1 --rMin -20 --rMax 20
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --robustFit=1 --doFits --robustHesse 1 --rMin -20 --rMax 20 --parallel 32
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 -o {name}_impacts.json --rMin -20 --rMax 20
plotImpacts.py -i {name}_impacts.json -o {name}_impacts --per-page 40
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
    script_file = os.path.join(output_dir, output_prefix + '_run_impacts.sh')
    with open(script_file, 'w') as f:
        f.write(script)
      
    st = os.stat(script_file)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

os.chdir( os.path.join(cmssw_base) )
