#! /bin/env python

# Python imports
import os, sys, stat, argparse, getpass, json
from datetime import datetime
from math import sqrt
import yaml
from collections import OrderedDict

# to prevent pyroot to hijack argparse we need to go around
tmpargv = sys.argv[:] 
sys.argv = []

# ROOT imports
import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True
sys.argv = tmpargv

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

cmssw_base = os.environ['CMSSW_BASE']

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'True'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'False'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='Create shape datacards ready for combine')

parser.add_argument('-p', '--path', action='store', dest='root_path', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/hists/histos_for_fitting_2017/', help='Directory containing rootfiles with the TH1 used for limit settings')
parser.add_argument('-l', '--luminosity', action='store', type=float, dest='luminosity', default=41529, help='Integrated luminosity (default is 41529 /pb)')
parser.add_argument('-le', '--luminosityError', action='store', type=float, dest='luminosityError', default=1.023, help='Error on the integrated luminosity (default is 1.023 /pb)')
parser.add_argument('-dataYear' , action='store', dest='dataYear', type=str, default='2017', help='Which year were the data taken? This has to be added in datacard entries in view of combination (avoid considering e.g. correlated lumi uncertainty accross years)')
parser.add_argument('-o', '--output', action='store', dest='output', type=str, default='datacards_2017', help='Output directory')
parser.add_argument('-c' , '--channel', action='store', dest='channel', type=str, default='all', help='Channel: el, mu, or all.')
parser.add_argument('-s' , '--selection', action='store', dest='selection', type=str, default='S3', help='Step: S0, S1, S2 or S3.')
parser.add_argument('-applyxsec' , action='store', dest='applyxsec', type=bool, default=True, help='Reweight MC processes by Xsec/Nevt from yml config.')
parser.add_argument('-xsecfile' , action='store', dest='xsecfile', type=str, default=cmssw_base+'/src/UserCode/FCNCLimits/xsec_txt/files17.yml', help='YAML config file path with Xsec and Nevt.')
parser.add_argument('--reweight', action='store_true', dest='reweight', help='Apply a preliminary reweighting. Not implemented yet.')
parser.add_argument('--fake-data', action='store_true', dest='fake_data', help='Use fake data instead of real data')
parser.add_argument('--SF', action='store_true', dest='SF', help='Produce cards for scale factors extraction (add line with rateParam). Not final yet!')
parser.add_argument('--nosys', action='store', dest='nosys', default=False, help='Consider or not systematic uncertainties (NB : bbb uncertainty is with another flag)')
parser.add_argument('--sysToAvoid', action='store', dest='sysToAvoid', nargs='+', default=[], help='Set it to exclude some of the systematics. Name should as in rootfile without the up/dowm postfix')
# Example to call it: python prepareShapesAndCards.py --sysToAvoid pu hf
parser.add_argument('--sysForSMtt', action='store', dest='sysForSMtt', nargs='+', default=['sw', 'tune', 'ps', 'pdf','hdamp'], help='Systematics affecting only SM tt.')
parser.add_argument('--correlatedSys', action='store', dest='correlatedSys', nargs='+', default=['sw', 'tune', 'ps', 'pdf', 'hdamp'], help='Systematics that are correlated accross years. NB: cross section unc are added by hand at the end of this script, go there to change correlation for them.')
parser.add_argument('--nobbb', action='store_false', help='Consider or not bin by bin MC stat systematic uncertainties')
parser.add_argument('--test', action='store_true', help='Do not prepare all categories, fasten the process for development')
parser.add_argument('-rebinning' , action='store', dest='rebinning', type=int, default=1, help='Rebin the histograms by -rebinning.')
parser.add_argument('-q', '--qcd', action='store', dest='qcd', type=str2bool, default=False, help='Estimate QCD')
parser.add_argument('-qi', '--qcdinput', action='store', dest='qcdinput', type=str, default='hist_dataDriven_QCD.root', help='Set QCD input file')

options = parser.parse_args()

channel_mapping = {"mu":'Ch0', "el":'Ch1', "all":'Ch2'}

channel = options.channel
selection= options.selection
individual_discriminants = { 
        # support regex (allow to avoid ambiguities if many histogram contains same patterns)
        # 'yields': get_hist_regex('yields(?!(_sf|_df))'),
        #'bb_DeltaR': get_hist_regex('h_keras_RecoAddbJetDeltaR_{0}_{1}'.format(channel_mapping[channel],selection)),
        #'qcd_mTrans': get_hist_regex('h_TransverseMass_{0}_{1}'.format(channel_mapping[channel],selection)),
        #'bb_DeltaR' : get_hist_regex('h_mindR_RecoAddbJetDeltaR_{0}_{1}'.format(channel_mapping[channel],selection)),
        #'bb_InvMass':get_hist_regex('h_mindR_RecoAddbJetInvMass_{0}_{1}'.format(channel_mapping[channel],selection)),
        #'bb_DeltaR_sp' : get_hist_regex('h_mindR_RecoAddbJetDeltaR3_{0}_{1}'.format(channel_mapping[channel],selection)),
        #'bb_InvMass_sp':get_hist_regex('h_mindR_RecoAddbJetInvMass3_{0}_{1}'.format(channel_mapping[channel],selection)),
        #'bb_2D_dRvsM':get_hist_regex('h_mindR_RecoDeltaRvsInvMass_spread_{0}_{1}'.format(channel_mapping[channel],selection)),
        }
discriminants = {
        # 'name of datacard' : list of tuple with 
        # (dicriminant ID, name in 'individual_discriminants' dictionary above).
        # Make sure the 'name of datacard' ends with '_categoryName (for plot step)
        #'bb_DeltaR':[(1, 'bb_DeltaR')],
        #'bb_InvMass':[(1, 'bb_InvMass')],
        #'bb_2D_dRvsM':[(1, 'bb_2D_dRvsM')],
        #'bb_All':[(1, 'bb_DeltaR_sp'),(1, 'bb_InvMass_sp')],
        }
for ibin in range(0,5):
    discriminants['dR_bin'+str(ibin)] = [(1, 'dR_bin'+str(ibin))]
    individual_discriminants['dR_bin'+str(ibin)] = get_hist_regex('h_mindR_RecoDeltaRvsJetPt_bin{0}_{1}_{2}'.format(ibin, channel_mapping[channel], selection))

for ibin in range(0,8):
    discriminants['M_bin'+str(ibin)] = [(1, 'M_bin'+str(ibin))]
    individual_discriminants['M_bin'+str(ibin)] = get_hist_regex('h_mindR_RecoInvMassvsJetPt_bin{0}_{1}_{2}'.format(ibin, channel_mapping[channel], selection))

if options.qcd:
    discriminants = {'qcd_mTrans':[(1, 'qcd_mTrans')]}

if options.test:
    discriminants = {'qcd_mTrans':[(1, 'bJetDisc_0')]}

# Our definition of Bkg
mc_categories = ['ttbb', 'ttbj', 'ccLF', 'ttbkg', 'other', 'qcd']#, 'ttX', 'SingleT', 'WJets', 'ZJets', 'VV', 'qcd']
smTTlist = ['ttbj', 'ttcc', 'ttLF'] # for systematics affecting only SM tt

processes_mapping = {x:[] for x in mc_categories}
#if options.qcd:
#    processes_mapping = {'other':[]}
# QCD 
processes_mapping['qcd'] = [options.qcdinput]
# Data
if options.qcd:
    processes_mapping['data_el'] = ['hist_Nosys_DataSingleEG.root']
    processes_mapping['data_mu'] = ['hist_Nosys_DataSingleMu.root']
else:
    processes_mapping['data_el'] = ['hist_DataSingleEG.root']
    processes_mapping['data_mu'] = ['hist_DataSingleMu.root']
processes_mapping['data_all'] = processes_mapping['data_el'] + processes_mapping['data_mu'] 

xsec_txt = 'xsec_txt/'
if options.dataYear == '2016':
    xsec_txt += 'xsec16.txt'
if options.dataYear == '2017':
    xsec_txt += 'xsec17.txt'
if options.dataYear == '2018':
    xsec_txt += 'xsec18.txt'

with open(xsec_txt, 'r') as f:
    n = 1
    while True:
        line = f.readline()
        if not line: break
        if not n == 1:
            tmp = line.split(' ')
            sample = tmp[0]
            order = int(tmp[2])
            group = tmp[4][:-1]

            if order < 0 or 'QCD' in group:
                continue
            if any(i in group for i in ['ttcc', 'ttLF']):
                group = 'ccLF'
            if any(i in group for i in ['ttX', 'SingleT', 'WJets', 'ZJets', 'VV']):
                group = 'other'
            processes_mapping[group].append(sample)
        n += 1

# IF you change Bkg Def, don't forget to change also the backgrounds list in main and the systematics for cross sections
processes_mapping['data_obs'] = processes_mapping['data_%s'%channel]
processes_mapping.pop('data_el')
processes_mapping.pop('data_mu')
processes_mapping.pop('data_all')

print(processes_mapping)

nevts = {x:0.0 for x in mc_categories}
nevts['data_obs'] = 0.0

if options.fake_data:
  print "Fake data mode not implemented yet! Exitting..."
  sys.exit(1)

if options.applyxsec:
    # Read Xsec file
    with open(options.xsecfile, 'r') as xsec_file:
        xsec_data = yaml.load(xsec_file)
    if not xsec_data:
        print "Error loading the cross section file %s"%options.xsecfile
        sys.exit(1)
    
def main():
    """Main function"""
    global nevts
    if options.qcd:
        signals = ['qcd']
    else:
        signals = ['ttbb']
    backgrounds = [x for x in mc_categories if not x in signals]
    
    print "Signal: ", signals
    print "Background considered: ", backgrounds
    print "Discriminants: ", discriminants
    
    discriminants_per_signal = dict((key, value) for key, value in discriminants.iteritems())
    for discriminant in discriminants.keys():
        print "Running discriminant: ", discriminant
        prepareShapes(backgrounds, signals, discriminants[discriminant], discriminant)
        print "Number of events: ", nevts, 2
        nevts = nevts.fromkeys(nevts, 0.0)
   
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

    #if histogram.GetEntries() == 0:
    #    return

    # Rescale histogram to luminosity, if it's not data
    if not 'data' in process:
        #print "Rescaleing %s to lumi: "%process, options.luminosity
        histogram.Scale(options.luminosity)
    #print process, " ", histogram.GetTitle(), " ", destination, " ", histogram.GetNbinsX()
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

    print("Preparing ROOT file for %s..."%discriminant)

    output_filename = os.path.join(options.output, 'shapes_%s.root' % (discriminant))
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))

    files = [os.path.join(root_path, f) for f in os.listdir(root_path) if f.endswith('.root')]

    # Gather a list of inputs files for each process.
    # The key is the process identifier, the value is a list of files
    # If more than one file exist for a given process, the histograms of each file will
    # be merged together later
    processes_files = {}
    for process, paths in processes_map.items():
        process_files = []
        for path in paths:
            r = re.compile(path, re.IGNORECASE)
            process_files += [f for f in files if r.search(f)]
        if len(process_files) == 0:
          print 'Warning: no file found for %s'%process
        processes_files[process] = process_files
        print "Files found for %s: "%(process), [os.path.basename(filename) for filename in process_files]

    # Create the list of histograms (nominal + systematics) for each category
    # we are interested in.
    # The key is the category name, and the value is a list of histogram. The list will always
    # contain at least one histogram (the nominal histogram), and possibly more, two per systematic (up & down variation)
    histogram_names = {}
    for discriminant_tuple in categories_map[discriminant]:
        discriminant_name = discriminant_tuple[1]
        r = re.compile(individual_discriminants[discriminant_name], re.IGNORECASE)
        #f = ROOT.TFile.Open(processes_files.values()[0][0])
        #f = ROOT.TFile.Open(processes_files['ttbb'][0])
        if options.qcd:
            f = ROOT.TFile.Open(processes_files['qcd'][0])
        else:
            f = ROOT.TFile.Open(processes_files['ttbb'][0])
        histogram_names[discriminant_name] = [n.GetName() for n in f.GetListOfKeys() if r.search(n.GetName()) and not 'fsr' in n.GetName() and not 'isr' in n.GetName()]
        
        f.Close()
    #for category, histogram#_name in categories_map.items():
    #    r = re.compile(histogram_name, re.IGNORECASE)
    #    f = ROOT.TFile.Open(processes_files.values()[0][0])
    #    histogram_names[category] = [n.GetName() for n in f.GetListOfKeys() if r.search(n.GetName())]
    #    f.Close()

    # Extract list of systematics from the list of histograms derived above
    # This code assumes that *all* categories contains the same systematics (as it should)
    # The systematics list is extracted from the histogram list of the first category
    # The list of expanded histogram name is also extract (ie, regex -> full histogram name)
    
    systematics = set()
    histograms = {}
    systematics_regex = re.compile('__(.*)(up|down)$', re.IGNORECASE)
    for category, histogram_names in histogram_names.items():
        for histogram_name in histogram_names:
            m = systematics_regex.search(histogram_name)
            if m:
                # It's a systematic histogram
                systematics.add(m.group(1))
            else:
                nominal_name = histogram_name
                print nominal_name
                if category in histograms:
                    # Check that the regex used by the user only match 1 histogram
                    if histograms[category] != nominal_name:
                        raise Exception("The regular expression used for category %r matches more than one histogram: %r and %r" % (category, nominal_name, histograms[category]))
                histograms[category] = nominal_name
    print "Found the following systematics in rootfiles: ", systematics
    if options.sysToAvoid:
        for sysToAvoid in options.sysToAvoid:
            systematics.discard(sysToAvoid)
        print "After ignoring the one mentioned with sysToAvoid option: ", systematics

    cms_systematics = [CMSNamingConvention(s) for s in systematics]
    
    def dict_get(dict, name):
        if name in dict:
            return dict[name]
        else:
            return None
    # Create final shapes
    shapes = {}
    for category, original_histogram_name in histograms.items():
        shapes[category] = {}
        for process, process_files in processes_files.items():
            shapes[category][process] = {}
            for process_file in process_files:
                f = ROOT.TFile.Open(process_file)
                TH1 = f.Get(original_histogram_name)
                print process_file+ " "+str(TH1.Integral())
                process_file_basename = os.path.basename(process_file)
                if not TH1:
                    print "No histo named %s in %s. Exitting..."%(original_histogram_name, process_file)
                    sys.exit()
                if options.applyxsec and not 'data' in process:
                    xsec = xsec_data[process_file_basename]['cross-section']
                    nevt = xsec_data[process_file_basename]['generated-events']
                    #print "Applying cross sec and nevt on %s "%process_file_basename, xsec, " ", nevt, " --> ", xsec/float(nevt)
                    TH1.Scale((xsec)/float(nevt))
                if options.applyxsec and 'data' in process:
                    TH1.Scale(1)
                if options.reweight :
                    print 'Reweighting on the flight not implemented yet! Exitting...'
                    # if you implement it, don't forget also to scale TH1 for systematics
                    sys.exit(1)
                    if "ZJets" in process_file :
                        if not ('ZJetsToLL_M-10to50') in process_file:
                            print "Reweight ", process_file, " by 0.75950" 
                            TH1.Scale(0.75950)
                shapes[category][process]['nominal'] = merge_histograms(process, TH1, dict_get(shapes[category][process], 'nominal'))
                nevts[process] += TH1.Integral()
                
                if not "data" in process:
                    if not options.qcd and 'qcd' in process: continue
                    if options.qcd and not 'qcd' in process: continue
                    for systematic in systematics:
                        if systematic in options.sysForSMtt and not process in smTTlist:
                            continue
                        for variation in ['up', 'down']:
                            key = CMSNamingConvention(systematic) + variation.capitalize()
                            #print "Key: ", key
                            TH1_syst = f.Get(original_histogram_name + '__' + systematic + variation)
                            #if systematic in options.sysForSMtt and not process in smTTlist:
                            #    # Copy nominal TH1 in non SMtt processes for systematics affecting only SMtt (already scaled)
                            #    shapes[category][process][key] = merge_histograms(process, TH1, dict_get(shapes[category][process], key))
                            #    continue
                            if not TH1_syst:
                                print "No histo named %s in %s"%(original_histogram_name + '__' + systematic + variation, process_file_basename)
                                sys.exit()
                            if options.applyxsec and not 'data' in process:
                                #process_file_basename = os.path.basename(process_file)
                                #xsec = xsec_data[process_file_basename]['cross-section']
                                #nevt = xsec_data[process_file_basename]['generated-events']
                                TH1_syst.Scale((xsec)/float(nevt))
                            shapes[category][process][key] = merge_histograms(process, TH1_syst, dict_get(shapes[category][process], key))
                
                f.Close()

    output_file = ROOT.TFile.Open(output_filename, 'recreate')

    if options.fake_data:
        print "Fake data mode not implemented yet! Exitting..."
        sys.exit(1)
        for category, processes in shapes.items():
            fake_data = None
            for process, systematics_dict in processes.items():
                if not fake_data:
                    fake_data = systematics_dict['nominal'].Clone()
                    fake_data.SetDirectory(ROOT.nullptr)
                else:
                    fake_data.Add(systematics_dict['nominal'])
            processes['data_obs'] = {'nominal': fake_data}

    for category, processes in shapes.items():
        output_file.mkdir(category).cd()
        for process, systematics_ in processes.items():
            for systematic, histogram in systematics_.items():
                histogram.SetName(process if systematic == 'nominal' else process + '__' + systematic)
                histogram.Write()
        output_file.cd()

    output_file.Close()
    print("Done. File saved as %r" % output_filename)

    return output_filename, cms_systematics

def prepareShapes(backgrounds, signals, discriminant, discriminantName):
    # Backgrounds is a list of string of the considered backgrounds corresponding to entries in processes_mapping 
    # Signals is a list of string of the considered signals corresponding to entries in processes_mapping 
    # discriminant is the corresponding entry in the dictionary discriminants 

    print "Preparing shapes for %s..."%discriminant

    import CombineHarvester.CombineTools.ch as ch
    root_path = options.root_path

    file, systematics = prepareFile(processes_mapping, discriminants, root_path, discriminantName)
   
    print "File: ", file
    print "Systematics: ", systematics

    for signal in signals :
        cb = ch.CombineHarvester()
        cb.AddObservations(['*'], [''], ['_%s'%options.dataYear], [''], discriminant)
        cb.AddProcesses(['*'], [''], ['_%s'%options.dataYear], [''], backgrounds, discriminant, False)
        cb.AddProcesses(['*'], [''], ['_%s'%options.dataYear], [''], [signal], discriminant, True)

        # Systematics
        if not options.nosys:
            if options.qcd:
                #cb.cp().AddSyst(cb, 'CMS$ERA_qcdiso', 'shape', ch.SystMap('process')(['qcd'], 1.00))
                pass
            else:
                for systematic in systematics:
                    systematic_only_for_SMtt = False
                    for systSMtt in options.sysForSMtt:
                        if CMSNamingConvention(systSMtt) == systematic:
                            systematic_only_for_SMtt = True
                    if not systematic_only_for_SMtt:
                        cb.cp().AddSyst(cb, systematic, 'shape', ch.SystMap('process')([x for x in mc_categories if not 'qcd' in x], 1.00))
                    else:
                        #cb.cp().AddSyst(cb, '$PROCESS_'+systematic, 'shape', ch.SystMap('process')(['ttother', 'ttlf', 'ttbj', 'tthad', 'ttfullLep'], 1.00))
                        cb.cp().AddSyst(cb, systematic, 'shape', ch.SystMap('process')(smTTlist, 1.00))
#            cb.cp().AddSyst(cb, '$ERA_lumi', 'lnN', ch.SystMap('era')(['%s'%options.dataYear], options.luminosityError))
            #cb.cp().AddSyst(cb, 'CMS_qcd', 'lnN', ch.SystMap('process')(['qcd'], 1.5))
                cb.cp().AddSyst(cb, 'CMS$ERA_lumi', 'lnN', ch.SystMap()(options.luminosityError))
            #cb.cp().AddSyst(cb, 'tt_xsec', 'lnN', ch.SystMap('process')
            #        (['ttbj', 'ttcc', 'ttLF', 'ttbkg'], 1.055)
            #        )
            #cb.cp().AddSyst(cb, 'Other_xsec', 'lnN', ch.SystMap('process')
                    #(['SingleTop', 'ttV', 'Wjets', 'DYjets', 'VV', 'tth'], 1.1)
            #        (['other'], 1.1)
            #        )

        if options.SF :
            print "Background renormalization is deprecated! Exitting..."
            sys.exit(1)
            cb.cp().AddSyst(cb, 'SF_$PROCESS', 'rateParam', ch.SystMap('process')
                    (['ttbb'], 1.)
                    )

        # Import shapes from ROOT file
        cb.cp().backgrounds().ExtractShapes(file, '$BIN/$PROCESS', '$BIN/$PROCESS__$SYSTEMATIC')
        cb.cp().signals().ExtractShapes(file, '$BIN/$PROCESS', '$BIN/$PROCESS__$SYSTEMATIC')

        # Bin by bin uncertainties
        if not options.nobbb:
            print "Treating bbb"
            bbb = ch.BinByBinFactory()
            #bbb.SetAddThreshold(0.1).SetMergeThreshold(0.5).SetFixNorm(True)
            bbb.SetAddThreshold(0.1)
            bbb.AddBinByBin(cb.cp().backgrounds(), cb)
            bbb.AddBinByBin(cb.cp().signals(), cb)

        if options.nosys and options.nobbb : 
            cb.cp().AddSyst(cb, '$ERA_lumi', 'lnN', ch.SystMap('era')(['%s'%options.dataYear], 1.00001)) # Add a negligible systematic (chosen to be lumi) to trick combine

        output_prefix = '%s_Discriminant_%s' % (signal, discriminantName)

        output_dir = os.path.join(options.output, '%s' % (signal))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        #print cb.PrintAll()
        #print cb.PrintObs()
        #print cb.PrintProcs()
        #print cb.PrintSysts()
        #print cb.PrintParams()
        po_nevts = ''
        for process, value in nevts.items():
            po_nevts += '--PO '+str(process)+'='+str(round(value,2))+' '
        
        # Write card
        fake_mass = '173'
        datacard = os.path.join(output_dir, output_prefix + '.dat')
        print "Datacard: ", datacard
        print "Output: ", os.path.join(output_dir, output_prefix+'_shapes.root')
        root_input = ROOT.TFile(os.path.join(output_dir, output_prefix + '_shapes.root'), 'recreate')
        cb.cp().WriteDatacard(os.path.join(output_dir, output_prefix + '.dat'), root_input)
        #cb.cp().WriteDatacard(os.path.join(output_dir, output_prefix + '.dat'), os.path.join(output_dir, output_prefix + '_shapes.root'))
        #cb.cp().mass([fake_mass, "*"]).WriteDatacard([os.path.join(output_dir, output_prefix + '.dat')], [os.path.join(output_dir, output_prefix + '_shapes.root')])

        # Write small script for datacard checks
        workspace_file = os.path.basename(os.path.join(output_dir, output_prefix + '_combine_workspace.root'))
        script = """#! /bin/bash
# Run checks
echo combine -M MaxLikelihoodFit -t -1 --expectSignal 0 {datacard} -n fitDiagnostics_{name}_bkgOnly --rMin -20 --rMax 20
echo python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgOnly.root -g fitDiagnostics_{name}_bkgOnly_plots.root
#combine -M MaxLikelihoodFit -t -1 --expectSignal 0 {datacard} -n _{name}_bkgOnly --rMin -20 --rMax 20 #--plots
#python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgOnly.root -g fitDiagnostics_{name}_bkgOnly_plots.root
#python ../../printPulls.py fitDiagnostics_{name}_bkgOnly_plots.root
combine -M MaxLikelihoodFit -t -1 --expectSignal 1 {datacard} -n _{name}_bkgPlusSig --robustHesse 1 --robustFit=1 #--plots
python ../../../../HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgPlusSig.root -g fitDiagnostics_{name}_bkgPlusSig_plots.root
python ../../printPulls.py fitDiagnostics_{name}_bkgPlusSig_plots.root
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
        script_file = os.path.join(output_dir, output_prefix + '_run_closureChecks.sh')
        with open(script_file, 'w') as f:
            f.write(script)
        
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        # Write small script for impacts
        if options.qcd:
            script = """#! /bin/bash
# Run impacts
combineTool.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} --doInitialFit --robustFit=1 --robustHesse 1
combineTool.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} --robustFit=1 --robustHesse 1 --doFits --parallel 10 
combineTool.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} -o {name}_impacts.json
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_qcd --PO r_qcd
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_tt --PO r_other
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
        else:
            script = """#! /bin/bash
# Run impacts
combineTool.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} --doInitialFit --robustFit=1 --robustHesse 1
combineTool.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} --robustFit=1 --robustHesse 1 --doFits --parallel 10 
combineTool.py -M Impacts -d {name}_combine_workspace.root -m {fake_mass} -o {name}_impacts.json
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_qcd --PO r_ttbb
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_tt --PO r_ttbj
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_bbbj --PO r_ccLF
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_bbbj --PO r_ttbkg
plotImpacts.py -i {name}_impacts.json -o {name}_impacts_bbbj --PO r_other
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1))
        script_file = os.path.join(output_dir, output_prefix + '_run_impacts.sh')
        with open(script_file, 'w') as f:
            f.write(script)
        
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        # Write small script for postfit shapes
        if options.qcd:
            script = """#! /bin/bash
# Run fit
text2workspace.py {datacard} -m {fake_mass} -o {workspace_root} -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO 'map=qcd_mTrans/ttbb:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/ttbj:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/ttcc:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/ttLF:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/ttbkg:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/ttX:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/SingleT:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/WJets:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/ZJets:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/VV:r_other[1.0,0.6,1.4]' --PO 'map=qcd_mTrans/qcd:r_qcd[1.0,0.0,5.0]' 
combine -M MaxLikelihoodFit {workspace_root} -n _{name}_postfit --saveNormalizations --saveShapes --saveWithUncertainties --robustFit=1 #--robustHesse 1 -v 1
PostFitShapesFromWorkspace -w {name}_combine_workspace.root -d {datacard} -o postfit_shapes_{name}.root -f fitDiagnostics_{name}_postfit.root:fit_s --postfit --sampling
python ../../convertPostfitShapesForPlotIt.py -i postfit_shapes_{name}.root
$CMSSW_BASE/src/UserCode/plotIt/plotIt -o postfit_shapes_{name}_forPlotIt ../../config_forPlotIt/postfit_plotIt_config_ttbb_{year}_{discriminantName}.yml -y
""".format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1), year=options.dataYear, discriminantName=discriminantName, physOptions=po_nevts)
        else:
            for ibin in range(0,8):
                if 'bin'+str(ibin) in discriminantName:
                    binbin = 'Bin'+str(ibin) 
                    break

            # Write small script for postfit shapes
            script = """#! /bin/bash
# Run fit
text2workspace.py {datacard} -m {fake_mass} -o {workspace_root} -P HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel --PO 'map={discriminantName}/ttbb:r_ttbb{bin}[1.0,0.2,1.8]' --PO 'map={discriminantName}/ttbj:r_ttbj{bin}[1.0,0.2,1.8]' --PO 'map={discriminantName}/ccLF:r_ccLF{bin}[1.0,0.2,1.8]'  --PO 'map={discriminantName}/ttbkg:r_ttbkg{bin}[1.0,0.2,1.8]' --PO 'map={discriminantName}/other:r_other{bin}[1.0,0.2,1.8]' --PO 'map={discriminantName}/qcd:r_other{bin}[1.0,0.2,1.8]'
#text2workspace.py {datacard} -m {fake_mass} -o {workspace_root} -P HiggsAnalysis.CombinedLimit.ttbbFitModel:ttbbFitModel {physOptions}
combine -M MaxLikelihoodFit {workspace_root} -n _{name}_postfit --saveNormalizations --saveShapes --saveWithUncertainties --robustFit=1 #--robustHesse 1 -v 1 
PostFitShapesFromWorkspace -w {name}_combine_workspace.root -d {datacard} -o postfit_shapes_{name}.root -f fitDiagnostics_{name}_postfit.root:fit_s --postfit --sampling
python ../../convertPostfitShapesForPlotIt.py -i postfit_shapes_{name}.root
$CMSSW_BASE/src/UserCode/plotIt/plotIt -o postfit_shapes_{name}_forPlotIt ../../config_forPlotIt/postfit_plotIt_config_ttbb_{year}_{discriminantName}.yml -y
    """.format(workspace_root=workspace_file, datacard=os.path.basename(datacard), name=output_prefix, fake_mass=fake_mass, systematics=(0 if options.nosys else 1), year=options.dataYear, discriminantName=discriminantName, physOptions=po_nevts, bin=binbin)
            
        script_file = os.path.join(output_dir, output_prefix + '_run_postfit.sh')
        with open(script_file, 'w') as f:
            f.write(script)
        
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)
        
def CMSNamingConvention(syst):
    # Taken from https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsCombinationConventions
    # systlist = ['jec', 'jer', 'elidiso', 'muidiso', 'jjbtag', 'pu', 'trigeff']
    if syst not in options.correlatedSys:
        return 'CMS_' + options.dataYear + '_' + syst
    else:
        return 'CMS_' + syst
    #if syst == 'jec':
    #    return 'CMS_scale_j'
    #elif syst == 'jer': 
    #    return 'CMS_res_j'
    #elif syst == 'elidiso': 
    #    return 'CMS_eff_e'
    #elif syst == 'muidiso': 
    #    return 'CMS_eff_mu'
    #elif any(x in syst for x in ['lf', 'hf', 'lfstats1', 'lfstats2', 'hfstats1', 'hfstats2', 'cferr1', 'cferr2']): 
    #    return 'CMS_btag_%s'%syst
    #elif syst == 'pu': 
    #    return 'CMS_pu'
    #elif syst == 'trigeff': 
    #    return 'CMS_eff_trigger'
    #elif syst == 'pdf':
    #    return 'pdf'
    #elif syst == 'scale':
    #    return 'QCDscale'
    #else:
    #    return syst
#
# main
#
if __name__ == '__main__':
    main()

