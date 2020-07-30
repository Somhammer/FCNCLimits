import os, sys
import ROOT

print "Usage: python saveFitResultAsText.py directory rootfile"

directory = sys.argv[1]
rootfile = sys.argv[2]

f_in = ROOT.TFile.Open(os.path.join(directory, rootfile))
result = f_in.Get('fit_mdf')
result.Print()

