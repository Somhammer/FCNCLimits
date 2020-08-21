import os, sys
import math, array
import numpy as np

import ROOT

if int(sys.argv[1]) == 1:
    minD = float(sys.argv[2])
    maxD = float(sys.argv[3])
    n    = int(sys.argv[4])
    listDelta = [round(minD+(maxD-minD)/float(n)*float(i),3) for i in range(n)]
    print ' '.join(str(i) for i in listDelta)
elif int(sys.argv[1]) == 2:
    print os.getcwd()
    fInput = ROOT.TFile.Open(str(os.getcwd())+'/'+str(sys.argv[2]))
    fOutput = ROOT.TFile.Open(str(sys.argv[3]),'update')
    delta = float(sys.argv[4])

    fitResult = fInput.Get('fit_mdf')
    pars = fitResult.floatParsFinal()
    arglistPoi = ROOT.RooArgList('POIs')
    binNum = 1
    while True:
        poi = pars.find('unfold_%d' % binNum)
        if not poi: break
        arglistPoi.add(poi)
        binNum += 1
    print "Poi list:",arglistPoi.Print()
    covMatrix = fitResult.reducedCovarianceMatrix(arglistPoi)
    invCovMatrix = covMatrix.Clone().Invert()
    print "Reduced Covariance Matrix"
    covMatrix.Print()
    print "Inverse Reduced Covariance Matrix"
    invCovMatrix.Print()

    outTree = fOutput.Get('gcc')
    bDelta = array.array('d',[float(delta)]) 
    bCorr = []
    for idx in range(0, binNum-1):
        deno = covMatrix[idx][idx] * invCovMatrix[idx][idx]
        if deno < 1.0: corr = 0.
        else: corr = math.sqrt(1. - 1./deno)
        print "Correlation%d:"%idx,corr
        arrCorr = array.array('d', [corr])
        bCorr.append(arrCorr)

    if not outTree:
        print "Tree does not exist"
        outTree = ROOT.TTree('gcc', 'global correlation coefficient')
        outTree.Branch('delta', bDelta, 'delta/D')
        for idx in range(0, binNum-1):
            outTree.Branch('corr%d' % idx, bCorr[idx], 'corr%d/D' % idx)
    else:
        outTree.SetBranchAddress('delta',bDelta)
        for idx in range(0, binNum-1):
            outTree.SetBranchAddress('corr%d' % idx, bCorr[idx])

    outTree.Fill()
    fOutput.cd()
    outTree.Write("",ROOT.TObject.kOverwrite)
    #fOutput.Write()
    fOutput.Close()
    fInput.Close()
elif int(sys.argv[1]) == 3:
    # Draw GCC vs Delta (3) or return best delta (4)i
    chain = ROOT.TChain("gcc")
    chain.Add(str(os.getcwd())+'/'+str(sys.argv[2]))
    nBr = chain.GetNbranches()
    listBr = []
    tmp = chain.GetListOfBranches()
    for i in range(nBr):
        listBr.append(tmp[i].GetName())
    
    listDelta = []
    listGCC = []
    for i in xrange(chain.GetEntries()):
        chain.GetEntry(i)
        listCorr = []
        for branch in listBr:
            if 'delta' in branch:
                delta = chain.GetLeaf(branch).GetValue(0)
            else:
                listCorr.append(chain.GetLeaf(branch).GetValue(0))
        gcc = sum(listCorr)/(nBr - 1.)
        listDelta.append(delta)
        listGCC.append(gcc)
    
    c = ROOT.TCanvas('','',800,800)
    arrDelta = np.array(listDelta)
    arrGCC = np.array(listGCC)
    TGr = ROOT.TGraph(len(listDelta),arrDelta,arrGCC)
    TGr.GetXaxis().SetTitle("#delta")
    TGr.GetYaxis().SetTitle("Global correlation coefficient")
    TGr.SetMarkerStyle(20)
    TGr.Draw('AP')
    c.Print('GCC.pdf','pdf')
    idx = listGCC.index(min(listGCC))
    print listDelta[idx]
else:
    print "Please set the first argument as an positive integer less than 3"
