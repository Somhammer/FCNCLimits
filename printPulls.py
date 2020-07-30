import ROOT
import os, sys
ROOT.gROOT.SetBatch(ROOT.kTRUE)
rootfilename = sys.argv[1]
rootfile = ROOT.TFile(rootfilename)
canvas = ROOT.TCanvas()
rootfile.GetObject('nuisances', canvas)
print rootfilename
canvas.Print(rootfilename.replace(".root", ".png"))

