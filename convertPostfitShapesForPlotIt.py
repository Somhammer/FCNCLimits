#! /usr/bin/env python

import os, sys, argparse, math
import subprocess
import glob

# to prevent pyroot to hijack argparse we need to go around
tmpargv = sys.argv[:] 
sys.argv = []
# ROOT imports
from ROOT import gROOT, gSystem, PyConfig, TFile, TColor, TCanvas
gROOT.Reset()
gROOT.SetBatch()
PyConfig.IgnoreCommandLineOptions = True
sys.argv = tmpargv

def shift_hist(hist, by):
    for b in range(1, hist.GetNbinsX() + 1):
        hist.SetBinContent(b, hist.GetBinContent(b) + by * hist.GetBinError(b))
        hist.SetBinError(b, 0)

def remove_errors(hist):
    for b in range(1, hist.GetNbinsX() + 1):
        hist.SetBinError(b, 0)

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'True'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'False'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='Compute data/MC scale factors from a MaxLikelihoodFit')

parser.add_argument('-i', '--input', action='store', type=str, dest='input', help='Path to the ROOT file created by combine harvester', required=True)
parser.add_argument('-a', '--add', action='store', type=str2bool, dest='add', help='Hadd output root file for each category', required=False)

options = parser.parse_args()

output_dir = os.path.splitext(options.input)[0]+'_forPlotIt'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print "Creating ROOT files suitable for plotIt..."

# Compute scale factors

file = TFile.Open(options.input)

channels = set()
for k in file.GetListOfKeys():
    name = k.GetName().split('_')
    name.pop()
    channels.add('_'.join(name))

channels = list(channels)
print "Detected channels: ", channels

# Construct the list of processs
# Naming is 'category/bkg_name'

for channel in channels:
    print "Channel: ", channel
    processes = set()
    for proc in file.Get('%s_prefit' % channel).GetListOfKeys():
        processes.add(proc.GetName())

    for process in processes:
        print "    Process: ", process
        if any(i in process for i in ['data_obs', 'TotalBkg', 'TotalProcs', 'TotalSig']):
            output_filename = "%s_%s_postfit_histos.root" % (process, channel)
        else:
            output_filename = "%s_postfit_histos.root" % process
        plot_file = TFile.Open(os.path.join(output_dir, output_filename), 'recreate')

        nominal_postfit = file.Get('%s_postfit/%s' % (channel, process))
        nominal_postfit.SetName(channel)
        nominal_postfit.Write()

        if process != 'data_obs':# and not process.startswith('Hct') and not process.startswith('Hut'):
            nominal_postfit_up = nominal_postfit.Clone()
            nominal_postfit_up.SetName(channel + '__postfitup')
            shift_hist(nominal_postfit_up, 1)

            nominal_postfit_down = nominal_postfit.Clone()
            nominal_postfit_down.SetName(channel + '__postfitdown')
            shift_hist(nominal_postfit_down, -1)

            remove_errors(nominal_postfit)

            nominal_postfit_up.Write()
            nominal_postfit_down.Write()

        plot_file.Close()

if options.add:
    processes = set()
    for proc in file.Get('%s_prefit' % channels[0]).GetListOfKeys():
        temp = proc.GetName()
        temp = temp.replace('_'+channels[0], '')
        processes.add(temp)
    print processes
    for process in processes:
        output_filename = "%s_postfit_histos.root" % process
        cmd = ['hadd', os.path.join(output_dir, output_filename)] + glob.glob(output_dir+'/'+process+'_*')
        subprocess.call(cmd)

print("All done. Files saved in %r" % output_dir)

