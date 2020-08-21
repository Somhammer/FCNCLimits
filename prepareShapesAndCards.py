#! /bin/env python

import os, sys, stat, argparse, getpass, json
from datetime import datetime
from math import sqrt
import yaml
from collections import OrderedDict

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True

cmssw_base = os.environ['CMSSW_BASE']

hadNegBinForProcess = {}
def setNegativeBinsToZero(h, process):
    if not process in hadNegBinForProcess:
        hadNegBinForProcess[process] = False
    for i in range(1, h.GetNbinsX() + 1):
        if h.GetBinContent(i) < 0.:
            if not hadNegBinForProcess[process]:
                print 'Remove negative bin in TH1 %s for process %s'%(h.GetTitle(), process)
            hadNegBinForProcess[process] = True
            h.SetBinContent(i, 0.)

def get_hist_regex(r):
    return '^%s(__.*(up|down))?$' % r

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'True'): 
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'False'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def CMSNamingConvention(syst):
    # Taken from https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsCombinationConventions
    if syst not in options.correlatedSys:
        return 'CMS_' + options.dataYear + '_' + syst
    else:
        return 'CMS_' + syst

parser = argparse.ArgumentParser(description='Create shape datacards ready for combine')
parser.add_argument('-p', '--path', action='store', dest='root_path', type=str, default=cmssw_base+'/src/UserCode/ttbbDiffXsec/hists/root16_post/', help='Directory containing rootfiles with the TH1 usef for unfolding')
parser.add_argument('-l', '--luminosity', action='store', type=float, dest='luminosity', default=41529, help='Integrated luminosity (default is 41529 /pb)')
parser.add_argument('-le', '--luminosityError', action='store', type=float, dest='luminosityError', default=1.023, help='Error on the integrated luminosity (default is 1.023 /pb)')
parser.add_argument('-dataYear' , action='store', dest='dataYear', type=str, default='2017', help='Which year were the data taken? This has to be added in datacard entries in view of combination (avoid considering e.g. correlated lumi uncertainty accross years)')
parser.add_argument('-o', '--output', action='store', dest='output', type=str, default='datacards_2017', help='Output directory')
parser.add_argument('-c' , '--channel', action='store', dest='channel', type=str, default='Ch2', help='Channel: Ch0, Ch1, Ch2.')
parser.add_argument('-s' , '--selection', action='store', dest='selection', type=str, default='S3', help='Step: S0, S1, S2 or S3.')
parser.add_argument('-xsecfile' , action='store', dest='xsecfile', type=str, default=cmssw_base+'/src/UserCode/ttbbDiffXsec/xsec_txt/files16.yml', help='YAML config file path with Xsec and Nevt.')
parser.add_argument('--nosys', action='store', dest='nosys', default=False, help='Consider or not systematic uncertainties (NB : bbb uncertainty is with another flag)')
parser.add_argument('--sysToAvoid', action='store', dest='sysToAvoid', nargs='+', default=[], help='Set it to exclude some of the systematics. Name should as in rootfile without the up/dowm postfix')
parser.add_argument('--sysForSMtt', action='store', dest='sysForSMtt', nargs='+', default=['sw', 'tune', 'ps', 'pdf','hdamp'], help='Systematics affecting only SM tt.')
parser.add_argument('--sysForQCD', action='store', dest='sysForQCD', nargs='+', default=['qcdiso'], help='Systematics affecting only QCD.')
parser.add_argument('--correlatedSys', action='store', dest='correlatedSys', nargs='+', default=['sw', 'tune', 'ps', 'pdf', 'hdamp'], help='Systematics that are correlated accross years. NB: cross section unc are added by hand at the end of this script, go there to change correlation for them.')
parser.add_argument('--nobbb', action='store_false', help='Consider or not bin by bin MC stat systematic uncertainties')
parser.add_argument('--test', action='store_true', help='Do not prepare all categories, fasten the process for development')
parser.add_argument('-rebinning' , action='store', dest='rebinning', type=int, default=20, help='Rebin the histograms by -rebinning.')
parser.add_argument('-u', '--unfold', action='store', dest='unfold', type=str2bool, default=False, help='Unfold')
parser.add_argument('-m', '--matrix', action='store', dest='matrix', type=str, default='h_mindR_3DmatrixDeltaR', help='Unfold')
parser.add_argument('-g', '--gen', action='store', dest='gen', type=str, default='h_mindR_GenAddbJetDeltaR', help='Unfold')
parser.add_argument('-r', '--regmode', action='store', dest='regmode', type=int, default=2, help='Regularization mode')
parser.add_argument('-q', '--qcd', action='store', dest='qcd', type=str2bool, default=False, help='Estimate QCD')
parser.add_argument('-qi', '--qcdinput', action='store', dest='qcdinput', type=str, default='hist_dataDriven_QCD.root', help='Set QCD input file')

options = parser.parse_args()

channel = options.channel
selection = options.selection

individual_discriminants = {
        # support regex (allow to avoid ambiguities if many histogram contains same patterns)
        # 'yields': get_hist_regex('yields(?!(_sf|_df))'), 
        }
discriminants = {
        # 'name of datacard' : list of tuple with
        # (discriminant ID, name in 'individual discriminants' dictionary above).
        # Make sure the 'name of datacard' ends with '_categoryName' (for plot step)
        }
if options.qcd:
    individual_discriminant['qcd_mTrans'] = get_hist_regex('h_TransverseMass_{0}_{1}'.format(channel, selection))
    discriminants = {'qcd_mTrnas':[(1, 'qcd_mTrans')]}
else:
    discriminants['dR_All'] = []
    for ibin in range(0,5):
        individual_discriminants['dR_bin'+str(ibin)] = get_hist_regex('h_mindR_RecoDeltaRvsJetPt_bin{0}_{1}_{2}'.format(ibin, channel, selection))
        discriminants['dR_All'].append((1, 'dR_bin'+str(ibin)))

matrix = '{0}_{1}_{2}'.format(options.matrix, channel, selection)
gen    = '{0}_{1}_{2}'.format(options.gen, channel, selection)

mc_categories = ['ttbb', 'ttbj', 'ccLF', 'ttbkg', 'other', 'qcd']
smTTlist = ['ttbj', 'ccLF']

processes_mapping = {x:[] for x in mc_categories}
if options.qcd:
    processes_mapping['data_Ch0'] = ['hist_Nosys_DataSingleMu.root']
    processes_mapping['data_Ch1'] = ['hist_Nosys_DataSingleEG.root']
else:
    processes_mapping['data_Ch0'] = ['hist_DataSingleMu.root']
    processes_mapping['data_Ch1'] = ['hist_DataSingleEG.root']
processes_mapping['data_Ch2'] = processes_mapping['data_Ch0'] + processes_mapping['data_Ch1']
processes_mapping['data_obs'] = processes_mapping['data_%s' % channel ]
processes_mapping.pop('data_Ch0')
processes_mapping.pop('data_Ch1')
processes_mapping.pop('data_Ch2')
processes_mapping['qcd'].append(options.qcdinput)

with open(options.xsecfile, 'r') as xsec_file:
    xsec_data = yaml.load(xsec_file)
if not xsec_data:
    print "Error loading the cross section file %s" % options.xsecfile
    sys.exit(1)

for item in os.listdir(options.root_path):
    if not item in xsec_data: continue
    if any(i in item for i  in ['QCD','Data']): continue
    category = xsec_data[item]['group'][1:]
    if any(i in category for i in ['ttcc', 'ttLF']):
        category = 'ccLF'
    elif any(i in category for i in ['ttX', 'SingleT', 'WJets', 'ZJets', 'VV']):
        category = 'other'
    processes_mapping[category].append(item)

print "Input root files: ", processes_mapping

def merge_histograms(process, histogram, destination):
    """
    Merge two histograms together. If the destination histogram does not exist, it
    is created by cloning the input histogram

    Parameters:

    process         Name of the current process
    histogram       Pointer to TH1 to merge
    destination     Dict of destination histograms. The key is the current category.

    Return:
    The merged histogram
    """
    if not histogram:
        raise Exception('Missing histogram for %r. This should not happen.' % process)
    if not 'data' in process:
        histogram.Scale(options.luminosity)
    histogram.Rebin(options.rebinning)
    
    d = destination
    if not d:
        d = histogram.Clone()
        d.SetDirectory(ROOT.nullptr)
    else:
        d.Add(histogram)
    setNegativeBinsToZero(d, process)

    return d

def prepareFile(processes_map, categories_map, root_path, discriminant):
    """
    Prepare a ROOT file suitable for Combine Harvester.
    The structure is the following:
        1) Each observable is mapped to a subfolder. The name of the folder is the name of the observable
        2) Inside each folder, there's a bunch of histogram, one per background and signal hypothesis. The name of the histogram is the name of the background.
    """

    import re

    print("Preparing ROOT file for %s..." % discriminant)

    output_filename = os.path.join(options.output, 'shapes_%s.root' % discriminant )
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))

    files = [os.path.join(root_path, f) for f in os.listdir(root_path) if f.endswith('.root')]

    processes_files = {}
    for process, paths in processes_map.items():
        process_files = []
        for path in paths:
            r = re.compile(path, re.IGNORECASE)
            process_files += [f for f in files if r.search(f)]
        if len(process_files) == 0:
            print 'Warning: no file found for %s' % process
        processes_files[process] = process_files

    histogram_names = {}
    for discriminant_tuple in categories_map[discriminant]:
        discriminant_name = discriminant_tuple[1]
        r = re.compile(individual_discriminants[discriminant_name], re.IGNORECASE)
        if options.qcd:
            f = ROOT.TFile.Open(processes_files['qcd'][0])
        else:
            f = ROOT.TFile.Open(processes_files['ttbb'][0])
        histogram_names[discriminant_name] = [n.GetName() for n in f.GetListOfKeys() if r.search(n.GetName())]
        f.Close()

    systematics = set()
    histograms = {}
    systematics_regex = re.compile('__(.*)(up|down)$', re.IGNORECASE)
    for category, histogram_names in histogram_names.items():
        for histogram_name in histogram_names:
            m = systematics_regex.search(histogram_name)
            if m:
                if 'isr' in m.group(1) or 'fsr' in m.group(1): continue
                systematics.add(m.group(1))
            else:
                nominal_name = histogram_name
                if category in histograms:
                    if histogrmas[category] != nominal_name:
                        raise Exception('The regular expression used for category %r mathces more than one histogram: %r and %r' % (category, nominal_name, histograms[category]))
                histograms[category] = nominal_name
    #systematics.add('qcdiso')
    print 'Found the following systematics in rootfiles: ', systematics
    if options.sysToAvoid:
        for sysToAvoid in options.sysToAvoid:
            systematics.discard(sysToAvoid)
        print 'After ignoring the one mentioned with sysToAvoid option:', systematics

    cms_systematics = [CMSNamingConvention(s) for s in systematics]

    def dict_get(dict, name):
        if name in dict:
            return dict[name]
        else:
            return None

    shapes = {}
    i = 1
    for category, original_histogram_name in histograms.items():
        shapes[category] = {}
        for process, process_files in processes_files.items():
            shapes[category][process] = {}
            if options.matrix and 'ttbb' in process: continue 
            for process_file in process_files:
                f = ROOT.TFile.Open(process_file)
                TH1 = f.Get(original_histogram_name)
                process_file_basename = os.path.basename(process_file)

                if not TH1:
                    print 'No histogram named %s in %s. Exitting...' % (original_histogram_name, process_file)
                    sys.exit()
                if not 'data' in process:
                    xsec = xsec_data[process_file_basename]['cross-section']
                    nevt = xsec_data[process_file_basename]['generated-events']
                    TH1.Scale(xsec/float(nevt))
                shapes[category][process]['nominal'] = merge_histograms(process, TH1, dict_get(shapes[category][process], 'nominal'))

                if not 'data' in process:
                    for systematic in systematics:
                        if systematic in options.sysForQCD and not 'qcd' in process: continue
                        if not systematic in options.sysForQCD and 'qcd' in process: continue
                        if systematic in options.sysForSMtt and not process in smTTlist: continue
                        for variation in ['up', 'down']:
                            key = CMSNamingConvention(systematic) + variation.capitalize()
                            TH1_syst = f.Get(original_histogram_name + '__' + systematic + variation)
                            if not TH1_syst:
                                print 'No histogram named %s in %s' % (original_histogram_name + '__' + systematic + variation, process_file_basename)
                                sys.exit()
                            TH1_syst.Scale(xsec/float(nevt))
                            shapes[category][process][key] = merge_histograms(process, TH1_syst, dict_get(shapes[category][process], key))
                f.Close()

    if options.matrix:
        ttbb_files = processes_files['ttbb']
        for ttbb_file in ttbb_files:
            ttbb_file_basename = os.path.basename(ttbb_file)
            xsec = xsec_data[ttbb_file_basename]['cross-section']
            nevt = xsec_data[ttbb_file_basename]['generated-events']
            f = ROOT.TFile.Open(ttbb_file)
            TH1 = f.Get(gen)
            TH1.Scale(options.luminosity*xsec/float(nevt))
            shapes['gen'] = {'ttbb':{'gen':TH1}}
            
            TH3 = f.Get(matrix)
            #TH3.Scale(1/TH3.Integral())
            TH3.Scale(options.luminosity*xsec/float(nevt))
            axisClone = (TH3.Project3D('z')).Clone()

            for xbin in range(1,TH3.GetNbinsX()+1):
                category = 'dR_bin%d' % (xbin-1)
                shapes[category]['ttbb']['nominal'] = []
                for ybin in range(1,TH3.GetNbinsY()+1):
                    TH1 = axisClone.Clone()
                    for zbin in range(1,TH3.GetNbinsZ()+1):
                        TH1.SetBinContent(zbin, TH3.GetBinContent(xbin,ybin,zbin))
                        TH1.SetBinError(zbin, TH3.GetBinError(xbin,ybin,zbin))
                        TH1.SetName('h_reco%d_gen%d' % (xbin, ybin))
                    TH1.Rebin(options.rebinning)
                    shapes[category]['ttbb']['nominal'].append(TH1)
            for systematic in systematics:
                if systematic in options.sysForQCD: continue
                for variation in ['up', 'down']:
                    key = CMSNamingConvention(systematic) + variation.capitalize()
                    TH3_syst = f.Get(matrix + '__' + systematic +variation)
                    if not TH3_syst:
                        print 'No histogram named %s in %s' % (original_histogram_name + '__' + systematic + variation, process_file_basename)
                        sys.exit()
                    #TH3_syst.Scale(1/TH3_syst.Integral())
                    TH3_syst.Scale(options.luminosity*xsec/float(nevt))
                    for xbin in range(1, TH3.GetNbinsX()+1):
                        category = 'dR_bin%d' % (xbin-1)
                        shapes[category]['ttbb'][key] = []
                        for ybin in range(1,TH3.GetNbinsY()+1):
                            TH1_syst = axisClone.Clone()
                            for zbin in range(1,TH3.GetNbinsZ()+1):
                                TH1_syst.SetBinContent(zbin, TH3_syst.GetBinContent(xbin,ybin,zbin))
                                TH1_syst.SetBinError(zbin, TH3.GetBinError(xbin,ybin,zbin))
                                TH1_syst.SetName('h_reco%d_gen%d__%s' % (xbin, ybin, systematic + variation))
                            TH1_syst.Rebin(options.rebinning)
                            shapes[category]['ttbb'][key].append(TH1_syst)

    output_file = ROOT.TFile.Open(output_filename, 'recreate')
    for category, processes in shapes.items():
        output_file.mkdir(category).cd()
        for process, systematics_ in processes.items():
            for systematic, histogram in systematics_.items():
                if options.matrix and 'ttbb' in process:
                    if 'gen' in category:
                        histogram.SetName(process+'_'+category)
                        histogram.Write()
                        continue
                    for hist in histogram:
                        histName = hist.GetName()
                        histName = histName.split('_')[2]
                        if systematic == 'nominal': name = process +'_'+ histName
                        else: name = process + '_' + histName + '__' + systematic
                        hist.SetName(name)
                        hist.Write()
                else:
                    histogram.SetName(process if systematic == 'nominal' else process + '__' + systematic)
                    histogram.Write()
        output_file.cd()
    output_file.Close()
    print 'Done. File saved as %r' % output_filename

    return output_filename, cms_systematics

def prepareShapes(backgrounds, signal, discriminant, discriminantName):
    # Backgrounds is a list of string of the considered backgrounds corresponding to entries in processes_mapping
    # Signal is a string of the considered signal corresponding to entries in processes_mapping
    # Discriminant is the corresponding entry in the dictionary discriminants

    print "Preparing shapes for %s..." % discriminant

    root_path = options.root_path

    file, systematics = prepareFile(processes_mapping, discriminants, root_path, discriminantName)
    output_prefix = '%s_Discriminant_%s' % (signal, discriminantName)
    output_dir = os.path.join(options.output, '%s' % signal)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    datacard = os.path.join(output_dir, output_prefix + '.dat')
    root_input = ROOT.TFile(os.path.join(output_dir, output_prefix + '_shapes.root'), 'recreate')

    print "========================================================================================================"
    print "Start writing datacard..."
    print "File:", file
    print "Systematics:", systematics
    print "Background: ", backgrounds
    print "Signal: ", signal
    print "Discriminant: ", discriminant
    if options.matrix:
        # Collect data, signal, background, gen level informations
        listColGen  = []
        listColData = []
        listColProc = []
        listRateParamSig = []
        listRateParamBkg = []
        listParamBkg = []
        listPoi = []

        strSigRateParamTemplate = "%s rateParam * %s* %lf [0.0,%lf]"
        strBkgRateParamTemplate = "%s rateParam %s %s 1.0 [0.0,10.0]"
        strBkgParamTemplate = "%s param 1.0 0.3"
        strPoiTemplate = "--PO 'map=%s:%s[%lf,0.0,%lf]'"

        file = ROOT.TFile.Open(file)
        root_input.cd()
        bkgIdx = 1
        sigIdx = 0
        for disc in discriminant:
            TH1 = file.Get(disc[1]+'/data_obs')
            TH1.SetName('data_obs_'+disc[1])
            TH1.Write()
            listColData.append({'bin':disc[1],'obs':TH1.Integral()})
            TH1_gen = file.Get('gen/ttbb_gen')
            for ibin in range(1,TH1_gen.GetNbinsX()+1):
                strGen = 'unfold_' + str(ibin)
                nevt = TH1_gen.GetBinContent(ibin)

                procName = signal+'_gen'+str(ibin)+'_'+disc[1]
                TH1 = file.Get(disc[1]+'/'+signal+'_gen'+str(ibin))
                TH1.SetName(procName+'_'+disc[1])
                TH1.Write()
                
                tmp = []
                for systematic in systematics:
                    variations = ['Up','Down']
                    for vari in variations:
                        TH1 = file.Get(disc[1]+'/'+signal+'_gen'+str(ibin)+'__'+systematic+vari)
                        TH1.SetName(procName+'_'+disc[1]+'__'+systematic+vari)
                        TH1.Write()
                    tmp.append('1')
                
                if sigIdx >= -2: 
                    listColGen.append({'bin':ibin,'poi':strGen,'nevt':nevt})
                    #listRateParamSig.append(strSigRateParamTemplate % (strGen, signal+'_gen'+str(ibin), nevt, 2*nevt))
                    listRateParamSig.append(strSigRateParamTemplate % (strGen, signal+'_gen'+str(ibin), 1.0, 10.0))
                    #listPoi.append(strPoiTemplate % (strGen, strGen, nevt, 2*nevt))
                    listPoi.append(strPoiTemplate % (strGen, strGen, 1.0, 10.0))
                listColProc.append({'bin':disc[1],'proc':procName,'procIdx':sigIdx,'rate':TH1.Integral(),'syst':tmp})
               
                sigIdx -= 1
            for background in backgrounds:
                procName = background+'_'+disc[1] 
                TH1 = file.Get(disc[1]+'/'+background)
                TH1.SetName(procName+'_'+disc[1])
                TH1.Write()

                tmp = []
                if 'qcd' in background:
                    for i in range(len(systematic)): tmp.append('-')
                    continue
                for systematic in systematics:
                    if any(i == systematic for i in [CMSNamingConvention(s) for s in ['sw','tune','ps','pdf','hdamp']]):
                        tmp.append('-')
                    else:
                        variations = ['Up','Down']
                        for vari in variations:
                            TH1 = file.Get(disc[1]+'/'+background+'__'+systematic+vari)
                            TH1.SetName(procName+'_'+disc[1]+'__'+systematic+vari)
                            TH1.Write()
                        tmp.append('1')
                listColProc.append({'bin':disc[1],'proc':procName,'procIdx':bkgIdx,'rate':TH1.Integral(),'syst':tmp})
                listRateParamBkg.append(strBkgRateParamTemplate % (procName, disc[1], procName,))
                listParamBkg.append(strBkgParamTemplate % (procName))
                bkgIdx += 1

        listRegularization = []

        strRegularizationTemplate = "constrReg%s constr %s delta[%lf]"
        
        listRegFactor = [ 
        [1.0],           # Type 1: Zero derivative - No regularization
        [1.0, -1.0],     # Type 2: First derivative
        [1.0, -2.0, 1.0] # Type 3: Second derivative
            ]

        for ibin in range(len(listColGen)):
            if len(listRegFactor[options.regmode]) > len(listColGen) - ibin: 
                break
            listRegFormula = []
            for idx, regFactor in enumerate(listRegFactor[options.regmode]):
                binNum = ibin + idx
                #listRegFormula.append("(%0.1lf)*(%s-%lf)" % (regFactor, listColGen[binNum]['poi'], listColGen[binNum]['nevt']))
                listRegFormula.append("(%0.1lf)*(%s-1.0)*%lf" % (regFactor, listColGen[binNum]['poi'], listColGen[binNum]['nevt']))
            listRegularization.append(strRegularizationTemplate % (ibin, '+'.join(s for s in listRegFormula), 1000.0))
       
        print "Regularization Formula: ", listRegularization
        
        listSyst = []
        listTheory = []
        listExp = []
        
        listSyst.append('CMS_%s_lumi lnN ' % (options.dataYear) + (str(options.luminosityError) + ' ') * len(listColProc))
        for idx, value in enumerate(systematics):
            if any(i == value for i in [CMSNamingConvention(s) for s in ['sw','tune','ps','pdf','hdamp']]):
                listTheory.append(value)
            else:
                listExp.append(value)
            strSyst = value + ' shape'
            for item in listColProc:
                strSyst += ' '+item['syst'][idx]
            listSyst.append(strSyst)
        print "Theory: ", listTheory
        print "Experiment: ", listExp
        strTheory = 'theory group = '+' '.join(item for item in listTheory)
        strExp    = 'syst group = '+' '.join(item for item in listExp)
        strSysGroup = strTheory +'\n' + strExp

        strDataCardTemplate = """
imax %(binnum)i
jmax %(procnum)i
kmax *
--------------------------------------------------------------------------------
shapes * * %(input_root)s $PROCESS_$CHANNEL $PROCESS_$CHANNEL__$SYSTEMATIC
--------------------------------------------------------------------------------
bin %(bins)s
observation %(observations)s
--------------------------------------------------------------------------------
bin %(listBin)s
process %(listProc)s
process %(listProcIdx)s
rate %(listNmc)s
--------------------------------------------------------------------------------
%(listSys)s
--------------------------------------------------------------------------------
%(rateParamMC)s
%(rateParamUnfold)s
%(paramMC)s
%(regularization)s
%(sysGroup)s
        """

        dictIn = {}
        dictIn['input_root'] = str(os.path.basename(os.path.join(output_dir, output_prefix + '_shapes.root')))
        dictIn['binnum'] = len(discriminant)
        dictIn['procnum'] = len(listColProc) - 1 
        dictIn['bins'] = ' '.join(d['bin'] for d in listColData)
        dictIn['observations'] = ' '.join(str(d['obs']) for d in listColData)
        dictIn['listBin'] = ' '.join(d['bin'] for d in listColProc)
        dictIn['listProc'] = ' '.join(d['proc'] for d in listColProc)
        dictIn['listProcIdx'] = ' '.join(str(d['procIdx']) for d in listColProc)
        dictIn['listNmc'] = ' '.join(str(d['rate']) for d in listColProc)
        dictIn['listSys'] = '\n'.join(item for item in listSyst)
        dictIn['rateParamMC'] = '\n'.join(item for item in listRateParamBkg)
        dictIn['rateParamUnfold'] = '\n'.join(item for item in listRateParamSig)
        dictIn['paramMC'] = '\n'.join(item for item in listParamBkg)
        dictIn['regularization'] = '\n'.join(item for item in listRegularization)
        dictIn['sysGroup'] = strSysGroup 

        strCardContent = strDataCardTemplate % dictIn
        with open(datacard, 'w') as fCard: fCard.write(strCardContent)

        pois = ' ' .join(item for item in listPoi)
        temp = ' -P '.join(d['poi'] for d in listColGen)
        minDelta = 0.1
        maxDelta = 1.0
        points = 20
        def deltaArray(minD, maxD, n):
            return [round(float(minDelta)+float(maxD)/float(n)*float(i),3) for i in range(n)]
        listDelta = deltaArray(minDelta,maxDelta,points)
        def listToShellArray(inList):
            return '('+' '.join(str(i) for i in listDelta)+')'
        combineOptions = '-M MultiDimFit -P %s --saveNLL --saveSpecifiedNuis=all --cminFinalHesse 1 --saveFitResult --setParameters delta=$testDelta' % temp
        strCombineTemplate = """
arrayDelta=$(python ../../computeGCC.py 1 {minDelta} {maxDelta} {points}) 
for testDelta in {tmp}
do
  combine %s -n RegTest {combineOptions}
  python ../../computeGCC.py 2 multiDimFitRegTest.root gcc.root $testDelta
done
bestDelta=$(../../computeGCC.py 3 gcc.root)
echo "Best delta: " $bestDelta
        """.format(tmp = '${arrayDelta[0]}',minDelta=minDelta,maxDelta=maxDelta,points=points, combineOptions=combineOptions)
        combineOptions = '-M MultiDimFit -P %s --saveNLL --saveSpecifiedNuis=all --cminFinalHesse 1 --saveFitResult --setParameters delta=$bestDelta' % temp

        if 'dR' in discriminantName:
            histName = 'h_mindR_RecoAddbJetDeltaR_{0}_{1}'.format(channel, selection) 
        elif 'M' in discriminantName:
            histName = 'h_mindR_RecoAddbJetInvMass_{0}_{1}'.format(channel, selection)
        else:
            print 'Wrong discriminant name, only deltaR and invarariant mass is usable'
            syst.exit(1)

        plottingCmd = """
python ../../makePostFitPlotsForPlotIt.py -d={discriminantName} -h={hist} -i=multidimfit_{name}_postfit.root -o=post_shapes_{name}_forPlotIt -y={year} -l={lumi} 
$CMSSW_BASE/src/UserCode/plotIt/plotIt -o post_spahes_{name}_forPlotIt ../../config_forPlotIt/postfit_plotIt_config_{discriminantName}.yml -y
        """.format(name=output_prefix, discriminantName=discriminantName, hist=histName, year=options.dataYear[-2:], lumi=options.luminosity)
    else:
        import CombineHarvester.CombineTools.ch as ch
        cb = ch.CombineHarvester()
        cb.AddObservations(['*'],[''],['_%s'%options.dataYear],[''],discriminant)
        cb.AddProcesses(['*'],[''],['_%s'%options.dataYear],[''],backgrounds,discriminant,False)
        cb.AddProcesses(['*'],[''],['_%s'%options.dataYear],[''],[signal],discriminant,True)
        if not options.nosys:
            cb.cp().AddSyst(cb, 'CMS$ERA_lumi', 'lnN', ch.SystMap()(options.luminosityError))
            for systematic in systematics:
                systematic_only_for_SMtt = False
                for systSMtt in options.sysForSMtt:
                    if CMSNamingConvention(systSMtt) == systematic:
                        systematic_only_for_SMtt = True
                if not systematic_only_for_SMtt:
                    cb.cp().AddSyst(cb, systematic, 'shape', ch.SystMap('process')([x for x in mc_categories if not 'qcd' in x], 1.00))
                else:
                    cb.cp().AddSyst(cb, systematic, 'shape', ch.SystMap('process')(smTTlist, 1.00))
        cb.cp().backgrounds().ExtractShapes(file, '$BIN/$PROCESS', '$BIN/$PROCESS__$SYSTEMATIC')
        cb.cp().signals().ExtractShapes(file, '$BIN/$PROCESS', '$BIN/$PROCESS__$SYSTEMATIC')
        cb.cp().WriteDatacard(datacard, root_input)
        
        strCombineTemplate = "# doing nothing for QCD %s"
        
        pois = ''
        strPoiTemplate = "--PO 'map=%s/%s:%s[%lf,%lf,%lf]'"
        for background in backgrounds:
            pois += strPoiTemplate % (discriminant, backgrounds, 'r_other', 1.0, 0.6, 1.4) + ' '
        pois += strPoiTemplate % (discriminant, signal, 'r_'+signal, 1.0, 0.0, 4.0)
        combineOptions = '-M FitDiagnostics --saveNormalizations --saveShapes --saveWithUncertainties --robustFit=1 --robustHesse 1 -v 1'
        plottingCmd = """
python ../../convertPostfitShapesForPlotIt.py -i post_shapes_{name}.root
$CMSSW_BASE/src/UserCode/plotIt/plotIt -o post_spahes_{name}_forPlotIt ../../config_forPlotIt/postfit_plotIt_config_ttbb_{year}_{discriminantName}.yml -y
        """.format(name=output_prefix, year=options.year, discriminantname=discriminantName)

    print "Datacard: ", datacard
    print "Output: ", os.path.join(output_dir, output_prefix + '.dat')
    # Write bash script
    ### Unfolding
    workspace_file = os.path.basename(os.path.join(output_dir, output_prefix + '_combine_workspace.root'))
    strScript = """
text2workspace.py {datacard} -m {fake_mass} -o {workspace_root} -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel {pois}
{regularization}
combine {workspace_root} -n _{name}_postfit {combineOptions}
{plottingCmd}
    """.format(datacard=os.path.basename(datacard), workspace_root=workspace_file, name=output_prefix, fake_mass=172.5, year=options.dataYear, discriminantName=discriminantName, regularization = strCombineTemplate % workspace_file, combineOptions=combineOptions, pois=pois, plottingCmd=plottingCmd)
    script_file = os.path.join(output_dir, output_prefix + '_run_postfit.sh')
    with open(script_file, 'w') as f:
        f.write(strScript)
    st = os.stat(script_file)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

    ### Impacts
    strScript = """
combineTools.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} --doInitialFit --robustFit=1 --robustHesse 1
combineTools.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} --robustFit=1 --robustHesse 1 --doFits --parallel 10
combineTools.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} -o {name}_impacts.json
{plottingCmd}
    """.format(datacard=os.path.basename(datacard), workspace_root=workspace_file, name=output_prefix, fake_mass=172.5, plottingCmd=plottingCmd)
    script_file = os.path.join(output_dir, output_prefix + '_run_impacts.sh')
    with open(script_file, 'w') as f:
        f.write(strScript)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

    #### Uncertainty breakdown
    strScript = """
#combine -M MultiDimFit --algo grid --points 100 {name}_combine_workspace.root -m 125 -n Nominal 
#combine -M MultiDimFit --algo none {name}_combine_workspace.root -m 125 -n bestfit --saveWorkspace
combine -M MultiDimFit --algo grid --points 50 -m 125 -n FreezeTheory higgsCombine.MultiDimFit.mH125.root --snapshotName MultiDimFit --freezeNuisanceGroups theory
combine -M MultiDimFit --algo grid --points 50 -m 125 -n FreezeTheorySyst higgsCombine.MultiDimFit.mH125.root --snapshotName MultiDimFit --freezeNuisanceGroups theory syst 
combine -M MultiDimFit --algo grid --points 50 -m 125 -n FreezeAll higgsCombine.MultiDimFit.mH125.root --snapshotName MultiDimFit --freezeNuisances all
#TheoryUnc^2 = TotalUnc^2 - FreezeTheory^2
#SystUnc^2 = FreezeTheoryUnc^2 - Freeze(Theory+Syst)Unc^2
#StatUnc^2 = Freeze(Theory+Syst)Unc^2 - FreezeAll^2
#plot1DScan.py option: others - FILE:LEGEND:COLOR
plot1DScan.py higgsCombine.MultiDimFit.mH125.root --output OnlyTotalUnc
plot1DScan.py higgsCombine.MultiDimFit.mH125.root --others 'higgsCombineTheory.MultiDimFit.mH125.root:Freeze th.:4' 'higgsCombineStat.MultiDimFit.mH125.root:Freeze all:2' --breakdown thoeory,syst,stat --output BreakdownAll 
    """.format(name=output_prefix)
    print listPoi
    script_file = os.path.join(output_dir, output_prefix + '_run_breakdown.sh')
    with open(script_file, 'w') as f:
        f.write(strScript)
    os.chmod(script_file, st.st_mode | stat.S_IEXEC)

def main():
    """Main Function"""
    if options.qcd:
        signal = 'qcd'
    else:
        signal = 'ttbb'
    backgrounds = [x for x in mc_categories if not x in signal]

    print "Signal:", signal
    print "Background considered:", backgrounds
    print "Discriminants:", discriminants

    for discriminant in discriminants.keys():
        print "Running discriminant:", discriminant
        prepareShapes(backgrounds, signal, discriminants[discriminant], discriminant)

if __name__ == '__main__':
    main()
