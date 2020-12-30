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

def gather_hists(self, output, discriminant, matrix):
    import re

    print "Preparing ROOT file for %s..." % discriminant

    output_filename = os.path.join(output, 'shapes_%s.root' % discriminant )
    if not os.path.exists(os.path.dirname(output_filename)):
        os.makedirs(os.path.dirname(output_filename))

    files = [os.path.join(self.root_path, f) for f in os.listdir(self.root_path) if f.endswith('.root')]

    processes_files = self._get_process_files(files) 
    histogram_names = self._get_hist_names(processes_files['ttbb'][0], discriminant)

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
    if self.ignore_syst:
        for syst in self.ignore_syst:
            systematics.discard(syst)
        print 'After ignoring the one mentioned with sysToAvoid option:', systematics

    cms_systematics = [ut.CMSNamingConvention(self.year, s, self.correlate_syst) for s in systematics]

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
            for process_file in process_files:
                f = ROOT.TFile.Open(process_file)
                TH1 = f.Get(original_histogram_name)
                process_file_basename = os.path.basename(process_file)

                if not TH1:
                    print 'No histogram named %s in %s. Exitting...' % (original_histogram_name, process_file)
                    sys.exit()
                if not 'data' in process:
                    xsec = self.xsec_data[process_file_basename]['cross-section']
                    nevt = self.xsec_data[process_file_basename]['generated-events']
                    TH1.Scale(xsec/float(nevt))
                shapes[category][process]['nominal'] = self._merge_histograms(process, TH1, dict_get(shapes[category][process], 'nominal'))

                if not 'data' in process:
                    for systematic in systematics:
                        if systematic in self.syst_for_qcd and not 'qcd' in process: continue
                        if not systematic in self.syst_for_qcd and 'qcd' in process: continue
                        if systematic in self.syst_for_tt and not process in self.ttbkg: continue
                        for variation in ['up', 'down']:
                            key = ut.CMSNamingConvention(self.year, systematic, self.correlate_syst) + variation.capitalize()
                            TH1_syst = f.Get(original_histogram_name + '__' + systematic + variation)
                            if not TH1_syst:
                                print 'No histogram named %s in %s' % (original_histogram_name + '__' + systematic + variation, process_file_basename)
                                sys.exit()
                            TH1_syst.Scale(xsec/float(nevt))
                            shapes[category][process][key] = self._merge_histograms(process, TH1_syst, dict_get(shapes[category][process], key))
                f.Close()

    if matrix:
        #self._get_projection_from3Dhist(unfold, self.processes_map[unfold[0]], histograms.keys(), discriminant, systematics)
        for signal in self.signals:
            for filename in self.processes_map[signal]:
                process_file_basename = os.path.basename(filename)
                xsec = self.xsec_data[process_file_basename]['cross-section']
                nevt = self.xsec_data[process_file_basename]['generated-events']

                f = ROOT.TFile.Open(os.path.join(self.root_path, filename))
                TH3 = f.Get(matrix)
                if not TH3:
                    print 'No histogram named %s in %s' % (matrix, process_file_basename)
                    sys.exit()
                TH3.Scale(xsec*self.luminosity/float(nevt))
                axisClone = (TH3.Project3D('z')).Clone()

                for idx, category in enumerate(histograms.keys()): # x-axis bin
                    shapes[category][signal] = {}
                    xbin = idx+1
                    shapes[category][signal]['nominal'] = []
                    for ybin in range(1,TH3.GetNbinsY()+1):
                        TH1 = axisClone.Clone()
                        for zbin in range(1,TH3.GetNbinsZ()+1):
                            TH1.SetBinContent(zbin, TH3.GetBinContent(xbin,ybin,zbin))
                            TH1.SetBinError(zbin, TH3.GetBinError(xbin,ybin,zbin))
                        TH1.SetName('h_reco%d_gen%d' % (xbin, ybin))
                        shapes[category][signal]['nominal'].append(TH1)

                for systematic in systematics:
                    if systematic in self.syst_for_qcd: continue
                    for variation in ['up', 'down']:
                        key = ut.CMSNamingConvention(self.year, systematic, self.correlate_syst) + variation.capitalize()
                        TH3_syst = f.Get(matrix + '__' + systematic +variation)
                        if not TH3_syst:
                            print 'No histogram named %s in %s' % (matrix + '__' + systematic + variation, process_file_basename)
                            sys.exit()
                        TH3_syst.Scale(xsec*self.luminosity/float(nevt))
                        for idx, category in enumerate(histograms.keys()):
                            xbin = idx + 1
                            shapes[category][signal][key] = []
                            for ybin in range(1,TH3.GetNbinsY()+1):
                                TH1_syst = axisClone.Clone()
                                for zbin in range(1,TH3.GetNbinsZ()+1):
                                    TH1_syst.SetBinContent(zbin, TH3_syst.GetBinContent(xbin,ybin,zbin))
                                    TH1_syst.SetBinError(zbin, TH3.GetBinError(xbin,ybin,zbin))
                                TH1_syst.SetName('h_reco%d_gen%d__%s' % (xbin, ybin, systematic + variation))
                                #TH1_syst.Rebin(options.rebinning)
                                shapes[category][signal][key].append(TH1_syst)

    output_file = ROOT.TFile.Open(output_filename, 'recreate')
    for category, processes in shapes.items():
        output_file.mkdir(category).cd()
        for process, systematics_ in processes.items():
            for systematic, histogram in systematics_.items():
                if matrix and 'ttbb' in process:
                    for hist in histogram:
                        histName = hist.GetName()
                        histName = histName.split('_')[2]
                        if systematic == 'nominal': name = process + '_' + histName
                        elif systematic == 'shape': name = 'shape_' + histName
                        else: name = process + '_' + histName + '__' + systematic
                        hist.SetName(name)
                        hist.Write()
                else:
                    histogram.SetName(process if systematic == 'nominal' else process + '__' + systematic)
                    histogram.Write()
        output_file.cd()
    output_file.Close()
    print 'Done. File saved as %r' % output_filename
    
    self.output_filename = output_filename
    self.systematics = cms_systematics
