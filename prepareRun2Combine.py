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

parser.add_argument('-p16', '--path16', action='store', dest='path_16', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/datacards_190702_2016_norebin', help='Directory containing data cards of 2016 analysis')
parser.add_argument('-p17', '--path17', action='store', dest='path_17', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/datacards_190702_2017', help='Directory containing data cards of 2017 analysis')
parser.add_argument('-p18', '--path18', action='store', dest='path_18', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/datacards_190702_2018', help='Directory containing data cards of 2018 analysis')
parser.add_argument('-o', '--output', action='store', dest='output', type=str, default='fullComb_190702_norebin_systDef_190702_190702', help='Output directory, please follow convention to distunguish input cards') 
parser.add_argument('--nosys', action='store', dest='nosys', default=False, help='Consider or not systematic uncertainties (NB : bbb uncertainty is with another flag)')

options = parser.parse_args()

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

for signal in ['Hct', 'Hut']:
  os.chdir( os.path.join(cmssw_base, 'src/UserCode/FCNCLimits/', options.output, signal) )
  card_name = 'FCNC_{}_Discriminant_DNN_{}_all.dat'.format(signal, signal)
  check_call('combineCards.py'+\
      ' year_2016=' + os.path.join(options.path_16, signal, card_name)+\
      ' year_2017=' + os.path.join(options.path_17, signal, card_name)+\
      ' year_2018=' + os.path.join(options.path_18, signal, card_name)+\
#      ' > ' +  os.path.join(options.output, signal) + '/FCNC_{}_Discriminant_DNN_{}_all_161718.dat'.format(signal, signal), shell=True)
      ' > FCNC_{}_Discriminant_DNN_{}_161718_all.dat'.format(signal, signal), shell=True)

  check_call('combineCards.py'+\
      ' year_2016=' + os.path.join(options.path_16, signal, card_name)+\
      ' year_2017=' + os.path.join(options.path_17, signal, card_name)+\
#      ' > ' +  os.path.join(options.output, signal) + '/FCNC_{}_Discriminant_DNN_{}_all_1617.dat'.format(signal, signal), shell=True)
      ' > FCNC_{}_Discriminant_DNN_{}_1617_b2j3.dat'.format(signal, signal), shell=True)
      #Trick to print all limits at once

  check_call('combineCards.py'+\
      ' year_2017=' + os.path.join(options.path_17, signal, card_name)+\
      ' year_2018=' + os.path.join(options.path_18, signal, card_name)+\
#      ' > ' +  os.path.join(options.output, signal) + '/FCNC_{}_Discriminant_DNN_{}_all_1718.dat'.format(signal, signal), shell=True)
      ' > FCNC_{}_Discriminant_DNN_{}_1718_b2j4.dat'.format(signal, signal), shell=True)


  # Backgrounds is a list of string of the considered backgrounds corresponding to entries in processes_mapping 
  # Signals is a list of string of the considered signals corresponding to entries in processes_mapping 
  # discriminant is the corresponding entry in the dictionary discriminants 

  output_prefix_list = ['FCNC_{}_Discriminant_DNN_{}_161718_all'.format(signal, signal),
                        'FCNC_{}_Discriminant_DNN_{}_1617_b2j3'.format(signal, signal),
                        'FCNC_{}_Discriminant_DNN_{}_1718_b2j4'.format(signal, signal),
                       ]

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

os.chdir( os.path.join(cmssw_base) )
#  # Write small script for datacard checks
#  script = """#! /bin/bash
#
## Run checks
#echo combine -M MaxLikelihoodFit -t -1 --expectSignal 0 {datacard} -n fitDiagnostics_{name}_bkgOnly
#echo python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgOnly.root -g fitDiagnostics_{name}_bkgOnly_plots.root
#combine -M MaxLikelihoodFit -t -1 --expectSignal 0 {datacard} -n _{name}_bkgOnly --rMin -20 --rMax 20
#python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgOnly.root -g fitDiagnostics_{name}_bkgOnly_plots.root
#python ../../printPulls.py fitDiagnostics_{name}_bkgOnly_plots.root
#combine -M MaxLikelihoodFit -t -1 --expectSignal 1 {datacard} -n _{name}_bkgPlusSig --rMin -20 --rMax 20
#python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgPlusSig.root -g fitDiagnostics_{name}_bkgPlusSig_plots.root
#python ../../printPulls.py fitDiagnostics_{name}_bkgPlusSig_plots.root
#""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
#  script_file = os.path.join(output_dir, output_prefix + '_run_closureChecks.sh')
#  with open(script_file, 'w') as f:
#      f.write(script)
#  
#  st = os.stat(script_file)
#  os.chmod(script_file, st.st_mode | stat.S_IEXEC)
#
#  # Write small script for impacts
#  script = """#! /bin/bash
#
## Run impacts
#combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --doInitialFit --robustFit 1
#combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --robustFit 1 --doFits --parallel 10
#combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 -o {name}_impacts.json
#plotImpacts.py -i {name}_impacts.json -o {name}_impacts
#""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
#    script_file = os.path.join(output_dir, output_prefix + '_run_impacts.sh')
#    with open(script_file, 'w') as f:
#        f.write(script)
#    
#    st = os.stat(script_file)
#    os.chmod(script_file, st.st_mode | stat.S_IEXEC)
