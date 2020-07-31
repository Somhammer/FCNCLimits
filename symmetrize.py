from ROOT import *
import ROOT
import os, sys

base_path = sys.argv[1]
f_in = sys.argv[2]

print "Start symmetrization on shapes..."

def symmetrize(var, var_opp, nom):

  for xbin in xrange(var.GetNbinsX()):
    if nom.GetBinContent(xbin+1) == 0: ratio = 1.
    else:
      ratio = var.GetBinContent(xbin+1) / nom.GetBinContent(xbin+1)
      ratio_opp = 1.
      if var_opp.GetBinContent(xbin+1) > 0: ratio_opp = var.GetBinContent(xbin+1) / var_opp.GetBinContent(xbin+1)

      diff = abs(nom.GetBinContent(xbin+1)-var.GetBinContent(xbin+1)) + abs(nom.GetBinContent(xbin+1)-var_opp.GetBinContent(xbin+1))
      if ratio_opp > 1.:
        var.SetBinContent(xbin+1, nom.GetBinContent(xbin+1) + diff/2.)
        if ratio > 1.2: var.SetBinContent(xbin+1, 1.2 * nom.GetBinContent(xbin+1))
      else:
        var.SetBinContent(xbin+1, nom.GetBinContent(xbin+1) - diff/2.)
        if ratio < 0.8: var.SetBinContent(xbin+1, 0.8 * nom.GetBinContent(xbin+1))
        if nom.GetBinContent(xbin+1) - diff/2. < 0.: var.SetBinContent(xbin+1, 0)

  return var


if not os.path.isfile(f_in.rstrip('.root') + '_org.root'):
  os.rename( f_in, f_in.rstrip('.root') + '_org.root' )

f = TFile.Open( f_in.rstrip('.root') + '_org.root', "READ")
f_new = TFile.Open( f_in, "RECREATE")

dir_list = []
dir_list = [x.GetName() for x in f.GetListOfKeys()]

for dir_ in dir_list:
  print dir_
  f_dir = f.Get(dir_)
  f_new.mkdir(dir_)
  f_new.cd(dir_)

  histo_list = []
  histo_list = [x.GetName() for x in f_dir.GetListOfKeys()]

  for histos in histo_list:
    h = f_dir.Get(histos)
    h.SetDirectory(ROOT.nullptr)
    hname = h.GetName()

    #Special treatements
    if ( any(low_stat in hname for low_stat in ['TuneCP5', 'hdamp'])
      or ('jer' in hname and any(name in hname for name in ['qcd','other']) and 'b2j3' in dir_ and '2017' in base_path)
      or ('pdf' in hname and 'b4j4' in dir_ and '2018' in base_path)
      or ('cferr1' in hname and 'ttcc' in hname and 'b4j4' in dir_) ):

      if 'Down' in hname:
        h_opp = f_dir.Get(hname.replace('Down','Up'))
      elif 'Up' in hname:
        h_opp = f_dir.Get(hname.replace('Up','Down'))
      h_opp.SetDirectory(ROOT.nullptr)

      h_nom = f_dir.Get(hname[:hname.rfind('__')])
      h_nom.SetDirectory(ROOT.nullptr)
      h = symmetrize(h, h_opp, h_nom)

    h.Write()

f_new.Write()
f_new.Close()
f.Close()
