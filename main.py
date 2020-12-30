import os, sys
import argparse
import yaml
import utils as ut

cmssw_base = os.environ['CMSSW_BASE']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create shape datacards ready for combine')
    parser.add_argument('-p', '--path', action='store', dest='root_path', type=str, default=cmssw_base+'/src/UserCode/ttbbDiffXsec/hists/root18_post/', help='Directory containing rootfiles with the TH1 usef for unfolding')
    parser.add_argument('-o', '--output', action='store', dest='output', type=str, default='datacards_2018', help='Output directory')
    parser.add_argument('-y', '--year', action='store', dest='year', type=str, default='18', help='')
    parser.add_argument('-l', '--luminosity', action='store', type=float, dest='luminosity', default=59741, help='Integrated luminosity (default is 35922 /pb)')
    parser.add_argument('-le', '--luminosityError', action='store', type=float, dest='luminosityError', default=1.025, help='Error on the integrated luminosity (default is 1.025 /pb)')
    parser.add_argument('-c' , '--channel', action='store', dest='channel', type=str, default='Ch2', help='Channel: Ch0, Ch1, Ch2.')
    parser.add_argument('-s' , '--selection', action='store', dest='selection', type=str, default='S7', help='Step: S0, S1, S2 or S3.')
    parser.add_argument('--nosys', action='store', dest='nosys', default=False, help='Consider or not systematic uncertainties (NB : bbb uncertainty is with another flag)')
    parser.add_argument('--sysToAvoid', action='store', dest='sysToAvoid', nargs='+', default=[], help='Set it to exclude some of the systematics. Name should as in rootfile without the up/dowm postfix')
    parser.add_argument('--sysForSMtt', action='store', dest='sysForSMtt', nargs='+', default=['sw', 'tune', 'ps', 'pdf','hdamp', 'tunecp5'], help='Systematics affecting only SM tt.')
    parser.add_argument('--sysForQCD', action='store', dest='sysForQCD', nargs='+', default=[], help='Systematics affecting only QCD.')
    parser.add_argument('--correlatedSys', action='store', dest='correlatedSys', nargs='+', default=['sw', 'tune', 'ps', 'pdf', 'hdamp', 'tunecp5'], help='Systematics that are correlated accross years. NB: cross section unc are added by hand at the end of this script, go there to change correlation for them.')
    parser.add_argument('--rebinning' , action='store', dest='rebinning', type=int, default=20, help='Rebin the histograms by -rebinning.')
    parser.add_argument('--xsecfile', action='store', dest='xsecfile', type=str, default=cmssw_base+'/src/UserCode/ttbbDiffXsec/devel/configs/files18.yml', help='YAML config file path with Xsec and Nevt.')
    parser.add_argument('--config', action='store', dest='config', type=str, default=cmssw_base+'/src/UserCode/ttbbDiffXsec/devel/configs/combine.yml', help='YAML config file path with combine options')

    options = parser.parse_args()

    channel = options.channel
    selection = options.selection
   
    with open(options.config, 'r') as f:
        config = yaml.load(f)
    if not options.config:
        print "Error loading the config file %s" % options.config
        sys.exit(1)

    groups = {
            # 'name of datacard' : list of tuple with
            # group name : (name, histogram regex).
            # Make sure the 'name of datacard' ends with '_categoryName' (for plot step)
            }
    for value in config['groups']:
        groups[value] = []
        for i in range(len(config['hist'][value])):
            hist_regex = ut.get_hist_regex('{0}_{1}_{2}'.format(config['hist'][value][i], channel, selection))
            groups[value].append(('bin'+str(i), hist_regex))

    matrix = {}
    if config['hist']['matrix'] is not None:
        for value in config['groups']:
            matrix[value] = '{0}_{1}_{2}'.format(config['hist']['matrix'][value], channel, selection)

    gen = {}
    if config['hist']['gen'] is not None:
        for value in config['groups']:
            gen[value] = '{0}_{1}_{2}'.format(config['hist']['gen'][value], channel, selection)

    mc_categories = config['mc']['ttbar']+config['mc']['others'] 
    signals = config['signals']
    backgrounds = [x for x in mc_categories if not x in signals]
    ttbkg = config['mc']['ttbar']

    with open(options.xsecfile, 'r') as f:
        xsec_data = yaml.load(f)
    if not xsec_data:
        print "Error loading the cross section file %s" % options.xsecfile
        sys.exit(1)

    processes_map = {x:[] for x in mc_categories}
    processes_map['data_Ch0'] = ['hist_DataSingleMu.root']
    processes_map['data_Ch1'] = ['hist_DataSingleEG.root']
    processes_map['data_Ch2'] = processes_map['data_Ch0'] + processes_map['data_Ch1']
    processes_map['data_obs'] = processes_map['data_%s' % channel ]
    processes_map.pop('data_Ch0')
    processes_map.pop('data_Ch1')
    processes_map.pop('data_Ch2')
    #processes_map['qcd'].append(options.qcdinput)

    for item in os.listdir(options.root_path):
        if not item in xsec_data: continue
        if any(i in item for i  in ['Data']): continue
        category = xsec_data[item]['group'][1:]
        if any(i in category for i in ['ttcc', 'ttLF']):
            category = 'ccLF'
        elif any(i in category for i in ['ttX', 'SingleT', 'WJets', 'ZJets', 'VV']):
            category = 'other'
        elif 'QCD' in category:
            category = 'qcd'
        processes_map[category].append(item)



    options_for_syst = {}
    for i in config['syst']:
        options_for_syst[i] = config['syst'][i]

    # DEBUG
    #print "Config:", config
    #print "Groups:", groups
    #print "Matrix:", matrix
    #print "Gen:", gen
    #print "Processes map:", processes_map
    #print "MC categories:", mc_categories
    #print "Signal:", signals
    #print "ttbar background:", ttbkg
    #print "Background considered:", backgrounds
    #print "Options for syst:", options_for_syst

    import prepareShapesAndCards as psc
    p = psc.PrepareShapesAndCards(options.year, options.luminosity, options.luminosityError, options.root_path)
    p.set_variables(groups)
    p.set_categories(signals, ttbkg, backgrounds)
    p.set_processes(processes_map, xsec_data)
    p.set_systs(options_for_syst)
   
    ### Prepare shapes
    for discriminant in groups.keys():
        print "Running discriminant:", discriminant
        p.gather_hists(options.output, discriminant, matrix[discriminant])
        if config['hist']['matrix'] is not None:
            datacard, pois = p.write_datacard_for_unfold(options.output, discriminant, config['fitOptions']['regularization'])
            p.write_script(datacard, options.output, discriminant, config['fitOptions'], pois)
        else:
            p.write_datacard_by_harvester()
