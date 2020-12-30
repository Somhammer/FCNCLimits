#! /bin/env python

import os, sys, stat, argparse, getpass, json
from datetime import datetime
from math import sqrt
import yaml
from collections import OrderedDict

import ROOT
ROOT.gROOT.SetBatch()
ROOT.PyConfig.IgnoreCommandLineOptions = True

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

def replace_str(text, start, length, replacement):
    return '%s%s%s' % (text[:start], replacement, text[start+length:])

def CMSNamingConvention(year, syst, correlated):
    # Taken from https://twiki.cern.ch/twiki/bin/view/CMS/HiggsWG/HiggsCombinationConventions
    if syst not in correlated:
        return 'CMS_' + year + '_' + syst
    else:
        return 'CMS_' + syst

