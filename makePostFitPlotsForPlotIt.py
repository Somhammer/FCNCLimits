import os, argparse
import yaml
import subprocess
from ROOT import *

parser = argparse.ArgumentParser(description='Set input root file')
parser.add_argument('-i', '--input', action='store', dest='input', type=str, default='...')
parser.add_argument('-x', '--xsecfile', action='store', dest='xsecfile', type=str, default='xsec_txt/files16.yml')
parser.add_argument('-r', '--root_path', action='store', dest='root_path', type=str, default='hists/root16_post')
options = parser.parse_args()

print "Usage: python saveFitResultAsText.py directory rootfile"
cmd = ['python', 'saveFitResultAsText.py', 'datacard_2016/ttbb', 'multidimfit_ttbb_Discriminant_dR_All_postfit.root']
with open('fitresult.txt','w') as f_out:
    subprocess.call(cmd, stdout=f_out)
with open(options.xsecfile, 'r') as xsec_file:
    xsec_data = yaml.load(xsec_file)

sigRates = []
bkgRates = [
#    {{'process':process, 'rate':rate},{'process':process, 'rate':rate}}
    ]

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

for item in os.listdir(options.root_path):
    if not item in xsec_data: continue
    if any(i in item for i in ['QCD','Data']): continue
    category = xsec_data[item]['group'][1:]
    if any(i in category for i in ['ttcc', 'ttLF']):
        category = 'ccLF'
    elif any(i in category for i in ['ttX', 'SingleT', 'WJets', 'ZJets', 'VV']):
        category = 'other'
    processes_mapping[category].append(item)

histName = "h_mindR_RecoAddbJetDeltaR_Ch2_S3"
for process, paths in processes_mapping.items():
    if 'data' in process:
        f_mu = TFile.Open(os.path.join(options.root_path,'hist_DataSingleMu.root'))
        f_el = TFile.Open(os.path.join(options.root_path,'hist_DataSingleEG.root'))
        TH1 = f_mu.Get('h_mindR_RecoAddbJetDeltaR_Ch0_S3')
        TH1.Add(f_el.Get('h_mindR_RecoAddbJetDeltaR_Ch1_S3'))
        TH1.SetName(histName)
        f_out = TFile.Open('./test/hist_data_obs.root','recreate')
        f_out.cd()
        TH1.Write()
    elif 'qcd' in process:
        f_in = TFile.Open(os.path.join(options.root_path,path))
        TH1 = f_in.Get(histName)
        f_out = TFile.Open('./test/'+path, 'recreate')
        f_out.cd()
        TH1.Write()
    else:
        for path in paths:
            f_in = TFile.Open(os.path.join(options.root_path,path))
            TH1 = f_in.Get(histName)
            xsec = xsec_data[path]['cross-section']
            nevt = xsec_data[path]['generated-events']
            #TH1.Scale(35922.0*xsec/float(nevt))
            if 'ttbb' in process:
                TH2 = f_in.Get("h_mindR_ResponseMatrixDeltaR_Ch2_S3") 
                for ibin in range(1, TH2.GetNbinsX()+1):
                    value = 0.0
                    for jbin in range(1, TH2.GetNbinsY()+1):
                        value += sigRates[jbin-1][0]*TH2.GetBinContent(ibin,jbin)
                    TH1.SetBinContent(ibin, value)
                    #TH1.SetBinError(ibin, error)
            else:
                for i in range(TH1.GetNbinsX()):
                    TH1.SetBinContent(i+1, TH1.GetBinContent(i+1)*bkgRates[i][process][0])
                    #TH1.SetBinError(i+1, TH1.GetBinError(i+1)*bkgRates[i][process][1])
            f_out = TFile.Open('./test/'+path,'recreate')
            f_out.cd()
            TH1.Write()
