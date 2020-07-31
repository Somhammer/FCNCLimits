import os, argparse
import yaml
import subprocess
from ROOT import *

cmssw_base = os.environ['CMSSW_BASE']

parser = argparse.ArgumentParser(description='Set input root file')
parser.add_argument('-d', '--discriminant', action='store', dest='disc', type=str, default='dR_All')
parser.add_argument('-h', '--histname', action='store', dest-'hist', type=str, default='test')
parser.add_argument('-i', '--input', action='store', dest='input', type=str, default='test')
parser.add_argument('-o', '--output', action='store', dest='output', type=str, default='test')
parser.add_argument('-y', '--year', action='store', dest='year', type=str, defalut='16')
parser.add_argument('-l', '--luminosity', action='store', dest='lumi', type=int default=35922)
options = parser.parse_args()

if not os.path.exists(options.output):
    os.makedirs(options.output)

tmp = cmssw_base+'/src/UserCode/ttbbDiffXsec/saveFitResultAsText.py'

cmd = ['python', tmp, os.getcwd(), 'multidimfit_ttbb_Discriminant_%s_postfit.root' % options.discriminant]
with open('fitresult.txt','w') as f_out:
    subprocess.call(cmd, stdout=f_out)

histPath = cmssw_base+'/src/UserCode/ttbbDiffXsec/hists/root%s_post' % options.year

with open(cmssw_base+'/src/UserCode/ttbbDiffXsec/xsec_txt/files%s.yml' % options.year, 'r') as xsec_file:
    xsec_data = yaml.load(xsec_file)

sigRates = []
bkgRates = []

with open('fitresult.txt','r') as f:
    flag = True
    while True:
        line = f.readline()
        if not line: break
        if '----' in line: flag = False
        if 'CMS' in line or '----' in line or flag: continue
        line = line.replace('\n','')
        temp = line.split(' ')
        temp = [v for v in temp if v]
        if len(temp) < 1: continue
        print temp
        process = temp[0].split('_')[0]
        bin = int((temp[0].split('_')[-1]).replace('bin',''))
        value = float(temp[1])
        error = float(temp[3])
        if 'unfold' in process:
            while len(sigRates) < bin: sigRates.append([])
            sigRates[bin-1] = [value, error]
        else:
            while len(bkgRates) < bin+1: bkgRates.append({})
            bkgRates[bin][process] = [value, error]
        print sigRates
        print bkgRates

mc_categories = ['ttbb', 'ttbj', 'ccLF', 'ttbkg', 'other', 'qcd']
processes_mapping = {x:[] for x in mc_categories}
processes_mapping['data_Ch0'] = ['hist_DataSingleMu.root']
processes_mapping['data_Ch1'] = ['hist_DataSingleEG.root']
processes_mapping['data_Ch2'] = processes_mapping['data_Ch0'] + processes_mapping['data_Ch1']
processes_mapping['data_obs'] = processes_mapping['data_Ch2' ]
processes_mapping.pop('data_Ch0')
processes_mapping.pop('data_Ch1')
processes_mapping.pop('data_Ch2')
processes_mapping['qcd'].append('hist_dataDriven_QCD.root')

for item in os.listdir(histPath):
    if not item in xsec_data: continue
    if any(i in item for i in ['QCD','Data']): continue
    category = xsec_data[item]['group'][1:]
    if any(i in category for i in ['ttcc', 'ttLF']):
        category = 'ccLF'
    elif any(i in category for i in ['ttX', 'SingleT', 'WJets', 'ZJets', 'VV']):
        category = 'other'
    processes_mapping[category].append(item)

histName = options.histname
for process, paths in processes_mapping.items():
    if 'data' in process:
        f_mu = TFile.Open(os.path.join(histPath,'hist_DataSingleMu.root'))
        f_el = TFile.Open(os.path.join(histPath,'hist_DataSingleEG.root'))
        muon = histName.replace('Ch2','Ch0')
        TH1 = f_mu.Get(histName.replace('Ch2','Ch0'))
        TH1.Add(f_el.Get(histName.replace('Ch2','Ch1')))
        TH1.SetName(histName)
        f_out = TFile.Open(options.output+'/hist_data_obs.root','recreate')
        f_out.cd()
        TH1.Write()
    elif 'qcd' in process:
        f_in = TFile.Open(os.path.join(histPath,path))
        TH1 = f_in.Get(histName)
        f_out = TFile.Open(options.output+'/'+path, 'recreate')
        f_out.cd()
        TH1.Write()
    else:
        for path in paths:
            f_in = TFile.Open(os.path.join(histPath,path))
            TH1 = f_in.Get(histName)
            
            f_out = TFile.Open(options.output+'/'+path,'recreate')
            f_out.cd()

            xsec = xsec_data[path]['cross-section']
            nevt = xsec_data[path]['generated-events']
            #TH1.Scale(35922.0*xsec/float(nevt))
            if 'ttbb' in process:
                TH2 = f_in.Get(histName.replace('RecoAddbJet','ResponseMatrix')) 
                TH2.Scale(1/TH2.Integral())
                for ibin in range(1, TH2.GetNbinsX()+1):
                    value = 0.0
                    total = 0.0
                    for i in range(len(sigRates)):
                        total += sigRates[i][0]
                    for jbin in range(1, TH2.GetNbinsY()+1):
                        value += total*TH2.GetBinContent(ibin,jbin)
                        #value += sigRates[jbin-1][0]*TH2.GetBinContent(ibin,jbin)
                    TH1.SetBinContent(ibin, value)
                    #TH1.SetBinError(ibin, error)
                TH1Gen = f_in.Get(histName.replace('Reco','Gen'))
                TH1Gen.Scale(options.lumi*xsec/float(nevt))
                for ibin in range(1, TH1Gen.GetNbinsX()+1):
                    TH1Gen.SetBinContent(ibin, sigRates[ibin-1][0])
                    TH1Gen.SetBinError(ibin, sigRates[ibin-1][1])
                f_out.cd()
                TH1Gen.Write()
            else:
                for i in range(TH1.GetNbinsX()):
                    TH1.SetBinContent(i+1, TH1.GetBinContent(i+1)*bkgRates[i][process][0])
                    TH1.SetBinError(i+1, TH1.GetBinError(i+1)*bkgRates[i][process][0])
            TH1.Write()
