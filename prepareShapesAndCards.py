#! /bin/env python

import os, sys, stat, argparse, getpass, json
from datetime import datetime
from math import sqrt
import yaml
from collections import OrderedDict

import re

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True

cmssw_base = os.environ['CMSSW_BASE']

import utils as ut
import templateCollection as tc

class PrepareShapesAndCards:
    def __init__(self, year, luminosity, luminosityError, root_path):
        self.year = year
        self.luminosity = luminosity
        self.luminosityError = luminosityError
        self.root_path = root_path

    from gatherhists import gather_hists
    from writecard import write_datacard_for_unfold
    from writecard import write_datacard_by_harvester
    from writescript import write_script

    def set_variables(self, groups):
        self.groups = groups

    def set_categories(self, signals, ttbkg, backgrounds):
        self.signals = signals
        self.ttbkg = ttbkg
        self.backgrounds = backgrounds

    def set_processes(self, processes_map, xsec_data):
        self.processes_map = processes_map
        self.xsec_data = xsec_data

    def set_systs(self, options_for_syst):
        self.ignore_syst = options_for_syst['ignore']
        self.syst_for_qcd = options_for_syst['qcd']
        self.syst_for_tt = options_for_syst['tt']
        self.correlate_syst = options_for_syst['correlate']
    
    def _merge_histograms(self, process, histogram, destination):
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
            histogram.Scale(self.luminosity)
        #histogram.Rebin(options.rebinning)
        
        d = destination
        if not d:
            d = histogram.Clone()
            d.SetDirectory(ROOT.nullptr)
        else:
            d.Add(histogram)
        ut.setNegativeBinsToZero(d, process)

        return d

    def _get_process_files(self, files):
        """
        Return the files corresponding to each process mapping.
        """
        processes_files = {}
        for process, paths in self.processes_map.items():
            process_files = []
            for path in paths:
                r = re.compile(path, re.IGNORECASE)
                process_files += [f for f in files if r.search(f)]
            if len(process_files) == 0:
                print 'Warning: no file found for %s' % process
            processes_files[process] = process_files

        return processes_files

    def _get_hist_names(self, filename, discriminant):
        """
        Return the dictionary which has histogram names for a one discriminant with all systematics
        """
        histogram_names = {}
        
        for discriminant_tuple in self.groups[discriminant]:
            r = re.compile(discriminant_tuple[1], re.IGNORECASE)
            f = ROOT.TFile.Open(filename)
            histogram_names[discriminant_tuple[0]] = [n.GetName() for n in f.GetListOfKeys() if r.search(n.GetName())]
            f.Close()
       
        return histogram_names
