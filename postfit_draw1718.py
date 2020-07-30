import sys, os
import re
from subprocess import call

if len(sys.argv) < 3:
  print("Directory of 2017 and 2018")
  sys.exit()
ver17 = sys.argv[1]
ver18 = sys.argv[2]

chs = ['Hct', 'Hut']
cmssw_base = os.environ['CMSSW_BASE']
plotit_path = os.path.join(cmssw_base, 'src/UserCode/HEPToolsFCNC/plotIt/plotIt')
config_path = os.path.join(cmssw_base, 'src/UserCode/FCNCLimits')
dest_folder = 'postfit_' + ver17.replace('datacards_','') + '_' + ver18.replace('datacards_','')
dest_path = os.path.join(cmssw_base, 'src/UserCode/FCNCLimits', dest_folder)

if not os.path.exists(dest_path):
  os.makedirs(dest_path)

for ch in chs:
  file_path_17 = os.path.join( ver17, ch, 'postfit_shapes_FCNC_' + ch + '_Discriminant_DNN_' + ch + '_all_forPlotIt/')
  file_path_18 = os.path.join( ver18, ch, 'postfit_shapes_FCNC_' + ch + '_Discriminant_DNN_' + ch + '_all_forPlotIt/')

  call(['hadd', '-f', dest_path + '/' + ch + '_postfit_histos.root', file_path_17 + ch + '_postfit_histos.root', file_path_18 + ch + '_postfit_histos.root'], shell=False)

  string_for_files = ''
  with open(config_path + '/postfit_file_' + ch + '.yml') as f:
    lines = f.readlines()
    skip_signal = False
    for line in lines:
      if skip_signal and 'hist' in line: skip_signal = False
      if ch + '_postfit_histos' in line: skip_signal = True
      if 'hist' in line:
        line = line[0] + file_path_17 + line[1:]
      if not skip_signal: string_for_files += line

  with open(config_path + '/postfit_file_' + ch + '.yml') as f:
    lines = f.readlines()
    skip_signal = False
    for line in lines:
      if skip_signal and 'hist' in line: skip_signal = False
      if ch + '_postfit_histos' in line: skip_signal = True
      if 'hist' in line:
        line = line[0] + file_path_18 + line[1:]
      if not skip_signal: string_for_files += line

  strings_for_signal = """'{0}/{1}_postfit_histos.root':
  type: signal
  pretty-name: '{1}'
  cross-section: 1
  generated-events: 1
  group: G{1}
  order: 0

""".format(dest_folder, ch)

  with open(config_path + '/postfit_file_' + ch + '_1718.yml', 'w+') as fnew:
    fnew.write(strings_for_signal)
    fnew.write(string_for_files)

  print 'Drawing 17+18 postfit distributions for ' + ch
  call([plotit_path, '-o ' + dest_path, config_path + '/postfit_plotIt_config_' + ch +'_1718.yml'], shell=False)
