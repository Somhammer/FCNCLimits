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

import utils as ut

def write_script(self, datacard, output, discriminant, config, pois=[]):
    print "Writing HCT scripts for %s..." % discriminant

    import templateCollection as tc

    for signal in self.signals:
        output_prefix = '%s_Discriminant_%s' % (signal, discriminant)
        workspace_file = output_prefix+'_combine_workspace.root'
 
        #strPoiTemplate = "--PO 'map={poi}:{poi}[{init},{min},{max}]'"
        strPoiTemplate = "--PO map='.*/{signal}_gen{bin}_*:{poi}[{init},{min},{max}]'"
        tmp = []
        for poi in pois:
            bin = poi[-1]
            tmp.append(strPoiTemplate.format(
                signal = signal, bin = bin, poi=poi, init=1.0, min=0.0, max=10.0))
        strWorkspace = tc.strTextToWorkspace.format(
            datacard = os.path.basename(datacard),
            workspace = workspace_file,
            model = config['bestfit']['model'], 
            pois = ' '.join(t for t in tmp))
        script_file = os.path.join(output, signal, output_prefix + '_make_workspace.sh')
        
        with open(script_file, 'w') as f:
            f.write(strWorkspace)
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)
    
        #commandOptions = ' '.join(tmp for tmp in config['base'])
        #if poiforCombine is not None: commandOptions += ' '+poiforCombine
        #if config['statOnly']: temp = 'statOnly'
        #else: temp = 'blinded'
        #commandOptions += ' ' + ' '.join(tmp for tmp in config['bestfit'][temp]['commands']) 
      
        ### Scan regularization parameter
        if config['regularization']['mode'] is not None:
#combine ttbb_Discriminant_deltaR_combine_workspace.root -n ScanReg -M MultiDimFit -m 125 --cminDefaultMinimizerTolerance 1e-2 --cminDefaultMinimizerStrategy 0 -t -1 --freezeParameters allConstrainedNuisances --setParameters delta=$testDelta --saveFitResult
            options = ' '.join(opt for opt in config['base']) + ' '
            options += ' '.join(opt for opt in config['regularization']['options']) + ' '
            options += ' '.join(opt for opt in config['regularization'][config['regularization']['minimize']])
            strCombine = tc.strCombine.format(
                workspace = workspace_file, outname = "ScanReg", options = options)
            strScript = tc.strScanRegularizationScript.format(
                minimize = config['regularization']['minimize'],
                minDelta = config['regularization']['minimum'], 
                maxDelta = config['regularization']['maximum'], 
                points   = config['regularization']['points'], 
                combine  = strCombine, outname = "ScanReg")
            script_file = os.path.join(output, signal, output_prefix + '_scan_regparams.sh')
            
            with open(script_file, 'w') as f:
                f.write(strScript)
            st = os.stat(script_file)
            os.chmod(script_file, st.st_mode | stat.S_IEXEC)
            delta = "bestDelta=$(python $CMSSW_BASE/src/UserCode/ttbbDiffXsec/compute{m}.py 3 {m}.root)".format(
                m = config['regularization']['minimize'])

        ### Toy test
        options = ' '.join(opt for opt in config['base']) + ' '
        options += ' '.join(opt for opt in config['bestfit']['options']) + ' '
        strCombine = tc.strCombine.format(
            workspace = workspace_file, outname = "_"+output_prefix+"_bkgPlusSig", options = options)
        if config['regularization']['mode'] is not None:
            strScript = delta
            strCombine += " --setParameters delta=$bestDelta"
        else:
            strScript = ""
        strScript += "\n" + tc.strToyTestTemplate.format(combine = strCombine, name = output_prefix)
        script_file = os.path.join(output, signal, output_prefix + '_run_toytest.sh')
        with open(script_file, 'w') as f:
            f.write(strScript)
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)
 
        ### Impacts
        strPois = '('+ ' '.join(item for item in pois) + ')'
        strScript = tc.strImpactTemplate.format(name = output_prefix, pois = strPois)
        script_file = os.path.join(output, signal, output_prefix + '_run_impacts.sh')
        with open(script_file, 'w') as f:
            f.write(strScript)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)
  
        ### Stat only fit

        ### Best fit
        strCombine = tc.strCombine.format(
            workspace = workspace_file, outname = output_prefix, options = options)
        if config['regularization']['mode'] is not None:
            strScript = delta
            strCombine += " --setParameters delta=$bestDelta"
        else:
            strScript = ""
        strScript += "\n" + strCombine
        script_file = os.path.join(output, signal, output_prefix + '_run_postfit.sh')
        with open(script_file, 'w') as f:
            f.write(strScript)
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

        ### Uncertainty breakdown
        # TheoryUnc^2 = TotalUnc^2 - FreezeTheory^2
        # SystUnc^2 = FreezeTheoryUnc^2 - Freeze(Theory+Syst)Unc^2
        # StatUnc^2 = Freeze(Theory+Syst)Unc^2 - FreezeAll^2
        # plot1DScan.py option: others - FILE:LEGEND:COLOR
        strSysts = ''
        with open(datacard, 'r') as f:
            lines = f.readlines()
            for line in lines[-2:]:
                tmp = line.split('=')
                strSysts += tmp[-1]
        strSysts = '(' + strSysts.replace('\n','')[1:] + ')'
        strScript = tc.strUncertaintyBreakdown.format(name=output_prefix, syst=strSysts, pois=strPois)
        script_file = os.path.join(output, signal, output_prefix + '_run_breakdown.sh')
        with open(script_file, 'w') as f:
            f.write(strScript)
        st = os.stat(script_file)
        os.chmod(script_file, st.st_mode | stat.S_IEXEC)

    print "Done. Scripts saved."
