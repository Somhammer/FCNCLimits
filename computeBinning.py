from rocCurveFacility import *
import os, sys, math
import ROOT

# Script to compute binning w.r.t. maximum significance in 2016-8 (easy to modifiy for ther purposes)
pathToTh1_2016 = "datacards_200101_2016v16_norebin"
pathToTh1_2017 = "datacards_200101_2017v16_norebin"
pathToTh1_2018 = "datacards_200101_2018v16_norebin"

ROOT.gROOT.SetBatch(ROOT.kTRUE)

def getBinning(partial_name, th1_rootFileName, coupling):
    th1_rootFile = ROOT.TFile(th1_rootFileName)

    #print th1_rootFile.Print()
    #print partial_name + "/" + coupling
    #print th1_rootFile.Get(partial_name + "/" + coupling)
    
    sig_th1 = th1_rootFile.Get(partial_name + "/" + coupling)
    
    ttbb_th1 = th1_rootFile.Get(partial_name + "/ttbb")
    ttlf_th1 = th1_rootFile.Get(partial_name + "/ttlf")
    ttcc_th1 = th1_rootFile.Get(partial_name + "/ttcc")
    other_th1 = th1_rootFile.Get(partial_name + "/other")
    bkg_th1 = ttbb_th1 + ttlf_th1 + ttcc_th1 + other_th1

    nbins = sig_th1.GetNbinsX()
    significances = []

    for i in xrange(nbins): #bin = 1 ~ nbins
        #tmp_sig = sig_th1.Integral(1,i+1)
        #tmp_bkg = bkg_th1.Integral(1,i+1)
        tmp_sig = sig_th1.Integral(i+1,nbins)
        tmp_bkg = bkg_th1.Integral(i+1,nbins)
        if tmp_bkg == 0: tmp_bkg = 0.000000001
        tmp_s = tmp_sig / math.sqrt(tmp_sig + tmp_bkg)
        significances.append(tmp_s)

    max_val = max(significances)
    max_idx = significances.index(max_val)
    max_val = round(max_val, 3)
    max_idx = -1.0 + (max_idx+1) * 2.0/nbins
    #max_idx = 1.0 - max_idx * 2.0/nbins

    return max_idx, max_val



#couplings = ['Hct', 'Hut']
couplings = ['Hct']
jetBins = ['b2j3', 'b3j3', 'b2j4', 'b3j4', 'b4j4']

for coupling in couplings:
    for jetBin in jetBins:
        title = "RocCurves_" + coupling  + "_" + jetBin

        partial_name = 'DNN_' + coupling + '_' + jetBin 

        th1_rootFileName_2016 = os.path.join(pathToTh1_2016, 'shapes_' + partial_name + '.root')
        bin_2016, val_2016 = getBinning(partial_name, th1_rootFileName_2016, coupling)
        print coupling + ' ' + jetBin + ' ' + '2016: ' + str(bin_2016) + '   ' + str(val_2016)

        th1_rootFileName_2017 = os.path.join(pathToTh1_2017, 'shapes_' + partial_name + '.root')
        bin_2017, val_2017 = getBinning(partial_name, th1_rootFileName_2017, coupling)
        print coupling + ' ' + jetBin + ' ' + '2017: ' + str(bin_2017) + '   ' + str(val_2017)

        th1_rootFileName_2018 = os.path.join(pathToTh1_2018, 'shapes_' + partial_name + '.root')
        bin_2018, val_2018 = getBinning(partial_name, th1_rootFileName_2018, coupling)
        print coupling + ' ' + jetBin + ' ' + '2018: ' + str(bin_2018) + '   ' + str(val_2018)
