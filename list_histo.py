from ROOT import *

file_name = '/afs/cern.ch/user/b/brfranco/work/public/FCNC/limits/rootfiles_for_limits/BDT_181120/hist_TTpowhegttcc.root'
rootfile = TFile(file_name)

histolist = rootfile.GetListOfKeys()
for key in histolist:
  #if 'h_LepPt' in key.GetName() and '__scale0' in key.GetName():
  #if 'h_LepPt_Ch1_S4' in key.GetName():
  #if '_Ch1_S4' in key.GetName() and '__' not in key.GetName():
  #if 'h_LepPt' in key.GetName() and '_Ch1_S4' in key.GetName():
  #if 'DNN' in key.GetName() and '__' not in key.GetName():
  #if '__' not in key.GetName():
  if 'Hut_j4b3_h_DNN_b2_Ch2' in key.GetName():
    print key.GetName()
