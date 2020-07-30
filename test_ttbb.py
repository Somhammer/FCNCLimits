from ROOT import *
import numpy as np
from subprocess import call

def MakeDatacard():
    strDataCardTemplate = """imax %(binnum)i
jmax %(procnum)i
kmax *
---------------
shapes * * %(inputroot)s hist_$PROCESS hist_$PROCESS__$SYSTEMATIC
---------------
bin %(listbin)s
observation %(listnumdata)s
---------------
bin     %(expandlistbin)s
process %(listproc)s
process %(listidxproc)s
rate    %(listnumproc)s
---------------
%(rateParams)s%(listConstr)s%(BBLOption)s%(listunc)s
"""

    strRateParamSigTemplate = "%s rateParam * *"
    strRateParamBkgTemplate = "%s rateParam * *"
    strRegularizationTemplate = ""
    strPOITemplate = ""
    strWorkspaceCmdTemplate = ""
    strRunCmdTemplate = ""

    histDir = './root16_post'
    listData = ['hist_DataSingleMu.root', 'hist_DataSingleEG.root']
    listMC = ['SingleTbar_tW_Powheg', 'SingleTbar_t_Powheg',
            'SingleTop_tW_Powheg', 'SingleTop_t_Powheg',
            'TTLJ_PowhegPythia_ttLF', 'TTLJ_PowhegPythia_ttbj',
            'TTLJ_PowhegPythia_ttcc', 'TTLJ_PowhegPythia_ttother',
            'TT_PowhegPythiaBkg', 'WJets_aMCatNLO',
            'WW_Pythia', 'WZ_Pythia', 'ZZ_Pythia',
            'ZJets_M10to50_aMCatNLO', 'ZJets_M50_aMCatNLO',
            'ttHbb_PowhegPythia', 'ttW_Madgraph', 'ttZ_Madgraph',
            'TTLJ_PowhegPythia_ttbb']

    dictData = {"mu":TFile.Open(histDir+'/hist_DataSingleMu.root'), "el":TFile.Open(histDir+'/hist_DataSingleEG.root')}
    dictMC = {x:TFile.Open(histDir+'/hist_'+x+'.root') for x in listMC}

    matrixName = 'h_mindR_3DmatrixDeltaR_Ch2_S3'

    h3_matrix = dictMC['TTLJ_PowhegPythia_ttbb'].Get(matrixName) # x: reco, y: gen, z: csv
    
    #### Normalization ####
    dictScale = {}
    genevt = {}
    with open('xsec_txt/genevt16.txt','r') as f:
        while True:
            line = f.readline()
            if not line: break
            tmp = line.split(' ')
            genevt[tmp[0]] = float(tmp[1])

    with open('xsec_txt/xsec16.txt', 'r') as f:
        n = 1
        while True:
            line = f.readline()
            if not line: break
            if n != 1:
                tmp = line.split(' ')
                sample = tmp[0]
                xsec = float(tmp[1])
                scale = float(35922)*xsec/genevt[sample]
                print sample + " " + str(scale)
                if 'QCD' in sample: continue
                dictScale[sample] = scale
            n += 1

    histBook = []
    listColProc = []
    listColData = []

    axisClone = (h3_matrix.Project3D("z")).Clone()
    for iRecoBin in range(1,h3_matrix.GetNbinsX()+1):
        tmp = dictData['mu'].Get('h_mindR_RecoDeltaRvsJetPt_bin%d_Ch0_S3' % (iRecoBin-1))
        tmp.Add(dictData['el'].Get('h_mindR_RecoDeltaRvsJetPt_bin%d_Ch1_S3' % (iRecoBin-1)))
        tmp.SetName('h_Reco%d_data_obs' % (iRecoBin))
        histBook.append(tmp)
        
        for iGenBin in range(1,h3_matrix.GetNbinsY()+1):
            tmp = axisClone.Clone()
            for iCSVBin in range(1,h3_matrix.GetNbinsZ()+1):
                tmp.SetBinContent(iCSVBin, h3_matrix.GetBinContent(iRecoBin,iGenBin,iCSVBin))
                tmp.SetBinError(iCSVBin, h3_matrix.GetBinContent(iRecoBin,iGenBin,iCSVBin))
            procName = "h_Reco%d_Gen%d" % (iRecoBin, iGenBin)
            tmp.SetName(procName)
            histBook.append(tmp)
        
        for key, value in dictMC.items():
            if 'ttbb' in key: continue
            tmp = value.Get('h_mindR_RecoDeltaRvsJetPt_bin%d_Ch2_S3' % (iRecoBin-1)) 
            procName = "h_Reco%d_Bkg%s" % (iRecoBin, key)
            tmp.SetName(procName)
            histBook.append(tmp)
            
    template = TFile.Open('template_ttbb.root', 'recreate')
    template.cd()
    for value in histBook:
        value.Write()
    template.Close()
MakeDatacard()
