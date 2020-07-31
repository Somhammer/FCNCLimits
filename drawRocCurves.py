from rocCurveFacility import *
import os, sys
import ROOT

# Script to draw 2016 and 2017 rocCurves on same graph (easy to modifiy for ther purposes)
pathToTh1_2016 = "datacards_200101_2016v16"
pathToTh1_2017 = "datacards_200101_2017v34"
pathToTh1_2018 = "datacards_200101_2018v34"
output_postfix = ''

if sys.argv[1]: output_postfix = sys.argv[1]

ROOT.gROOT.SetBatch(ROOT.kTRUE)

def getRocCurve(partial_name, th1_rootFileName, coupling):
    th1_rootFile = ROOT.TFile(th1_rootFileName)

    print th1_rootFile.Print()
    print partial_name + "/" + coupling
    print th1_rootFile.Get(partial_name + "/" + coupling)
    
    sig_th1 = th1_rootFile.Get(partial_name + "/" + coupling)
    sig_eff = drawEffVsCutCurve(sig_th1)
    
    ttbb_th1 = th1_rootFile.Get(partial_name + "/ttbb")
    ttlf_th1 = th1_rootFile.Get(partial_name + "/ttlf")
    ttcc_th1 = th1_rootFile.Get(partial_name + "/ttcc")
    other_th1 = th1_rootFile.Get(partial_name + "/other")
    bkg_th1 = ttbb_th1 + ttlf_th1 + ttcc_th1 + other_th1
    bkg_eff = drawEffVsCutCurve(bkg_th1)

    rocCurve = drawROCfromEffVsCutCurves(sig_eff, bkg_eff)
    return rocCurve



rocCurveOutputFolder = 'rocCurves_' + pathToTh1_2016.split('_')[1] + ('_') + pathToTh1_2017.split('_')[1] + ('_') + pathToTh1_2018.split('_')[1] + output_postfix

if not os.path.exists(rocCurveOutputFolder):
    os.mkdir(rocCurveOutputFolder)

couplings = ['Hct', 'Hut']
jetBins = ['b2j3', 'b3j3', 'b2j4', 'b3j4', 'b4j4']

for coupling in couplings:
    for jetBin in jetBins:
        title = "RocCurves_" + coupling  + "_" + jetBin
        canvas = ROOT.TCanvas(title, title)
        canvas.SetGrid()

        partial_name = 'DNN_' + coupling + '_' + jetBin 

        th1_rootFileName_2016 = os.path.join(pathToTh1_2016, 'shapes_' + partial_name + '.root')
        rocCurve_2016 = getRocCurve(partial_name, th1_rootFileName_2016, coupling)
        rocCurve_2016.SetTitle("ROC Curve: " + coupling + " " + jetBin)
        rocCurve_2016.GetXaxis().SetTitle("Background efficiency")
        rocCurve_2016.GetYaxis().SetTitle("Signal efficiency")
        rocCurve_2016.SetMarkerColor(ROOT.kBlue)
        rocCurve_2016.SetLineColor(ROOT.kBlue)
        rocCurve_2016.SetLineWidth(2)
        #rocCurve_2016.SetMarkerStyle(4)
        rocCurve_2016.Draw()

        th1_rootFileName_2017 = os.path.join(pathToTh1_2017, 'shapes_' + partial_name + '.root')
        rocCurve_2017 = getRocCurve(partial_name, th1_rootFileName_2017, coupling)
        rocCurve_2017.SetMarkerColor(ROOT.kRed)
        rocCurve_2017.SetLineColor(ROOT.kRed)
        rocCurve_2017.SetLineWidth(2)
        #rocCurve_2017.SetMarkerStyle(2)
        rocCurve_2017.Draw("same")

        th1_rootFileName_2018 = os.path.join(pathToTh1_2018, 'shapes_' + partial_name + '.root')
        rocCurve_2018 = getRocCurve(partial_name, th1_rootFileName_2018, coupling)
        rocCurve_2018.SetMarkerColor(8)
        rocCurve_2018.SetLineColor(8)
        rocCurve_2018.SetLineWidth(2)
        #rocCurve_2018.SetMarkerStyle(2)
        rocCurve_2018.Draw("same")

        

        legend = ROOT.TLegend(0.1, 0.7, 0.3, 0.9)
        legend.AddEntry(rocCurve_2016, "2016", "l")
        legend.AddEntry(rocCurve_2017, "2017", "l")
        legend.AddEntry(rocCurve_2018, "2018", "l")
        legend.Draw("")

        canvas.Print(os.path.join(rocCurveOutputFolder, title + ".png"))

