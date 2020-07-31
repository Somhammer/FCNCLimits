#! /usr/bin/env python

import os, sys, argparse, math

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


parser = argparse.ArgumentParser(description='Compute data/MC scale factors from a MaxLikelihoodFit')

parser.add_argument('-i', '--input', action='store', type=str, dest='input', help='Path to the ROOT file created by combine harvester', required=True)
parser.add_argument('-s', '--signals', action='store', type=str, dest='signals', help='Path to the ROOT file containing all the signal shapes')

options = parser.parse_args()

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

processs = set()

#for proc in file.Get('%s_prefit' % channels[0]).GetListOfKeys():
for proc in file.Get('%sb2j3_prefit' % channels[0][:-4]).GetListOfKeys():
    processs.add(proc.GetName())

print 'Detected processes: ', processs

output_dir = os.path.splitext(options.input)[0]+'_forPlotIt'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("")
print("Creating ROOT files suitable for plotIt...")

# Prepare shapes for plotIt
for process in processs:
    print "Process: ", process

    output_filename = "%s_postfit_histos.root" % (process)
    plot_file = TFile.Open(os.path.join(output_dir, output_filename), 'recreate')
    for channel in channels:
#        print "    Channel : ", channel
        # Nominal post-fit shape
        nominal_postfit = file.Get('%s_postfit/%s' % (channel, process))
        try:
            nominal_postfit.SetName(channel)
            nominal_postfit.Write()
            print "    Channel : ", channel

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

        except: pass

    plot_file.Close()

if options.signals:
    f = TFile.Open(options.signals)
    signals = [k.GetName() for k in f.Get(channels[0]).GetListOfKeys() if not '__' in k.GetName() and ('Hct' in k.GetName() or 'Hut' in k.GetName())]

    for signal in signals:

        output_filename = "%s_postfit_histos.root" % (signal)
        plot_file = TFile.Open(os.path.join(output_dir, output_filename), 'recreate')
        for channel in channels:
            shape = f.Get('%s/%s' % (channel, signal))
            shape.SetName(channel)
            shape.Write()

        plot_file.Close()

    f.Close()

print("All done. Files saved in %r" % output_dir)

