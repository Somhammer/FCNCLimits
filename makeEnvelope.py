#! /usr/bin/env python

import argparse
import re
import sys
import os

parser = argparse.ArgumentParser(description='Create scale variation systematics histograms.')

parser.add_argument('-d', '--directory', type=str, dest='directory', default='/home/seohyun/work/ttbb/ttbbRun2_dev/output/', help='The directory with ROOT input file containing histograms')
parser.add_argument('-s', '--syst', metavar='scale', nargs='+', default=['scale'], help='Name of the systematics of which the envelope is needed')

args = parser.parse_args()

import ROOT

def getEnvelopHistograms(nominal, variations):
    """
    Compute envelop histograms create by all variations histograms. The envelop is simply the maximum
    and minimum deviations from nominal for each bin of the distribution
    Arguments:
    nominal: The nominal histogram
    variations: a list of histograms to compute the envelop from
    """

    if len(variations) < 2:
        raise TypeError("At least two variations histograms must be provided")
    
    # Use GetNcells() so that it works also for 2D histograms
    n_bins = nominal.GetNcells()
    for v in variations:
        if v.GetNcells() != n_bins:
            raise RuntimeError("Variation histograms do not have the same binning as the nominal histogram")

    up = nominal.Clone()
    up.SetDirectory(ROOT.nullptr)
    up.Reset()

    down = nominal.Clone()
    down.SetDirectory(ROOT.nullptr)
    down.Reset()

    for i in range(0, n_bins):
        minimum = float("inf")
        maximum = float("-inf")

        for v in variations:
            c = v.GetBinContent(i)
            minimum = min(minimum, c)
            maximum = max(maximum, c)

        up.SetBinContent(i, maximum)
        down.SetBinContent(i, minimum)

    return (up, down)

files_to_compute_envelope = [os.path.join(args.directory, rootfile) for rootfile in os.listdir(args.directory) if rootfile.endswith('.root')]
for input in files_to_compute_envelope:

    print("Working on %r...") % input
    f = ROOT.TFile(input)
    if not f or f.IsZombie():
        continue

    envelopes = []

    for syst in args.syst:
        # List keys
        variations = {}
        for key in f.GetListOfKeys():
            if re.match(".*__{}[0-9]$".format(syst), key.GetName()) and not re.match(".*__{}up$".format(syst), key.GetName()) and not re.match(".*__{}down$".format(syst), key.GetName()):
                name = re.sub('__.*$', '', key.GetName())
                var = variations.setdefault(name, [])
                var.append(key.ReadObj())

        # Ensure we have all uncertainties
        to_remove = []
        for key, values in variations.items():
            if len(values) != 6:
                print("Warning: I was expecting 6 scale variations, but I got %d for %r" % (len(values), key))
                to_remove.append(key)

        for n in to_remove:
            del variations[n]

        if len(variations) == 0:
            print("Warning: no variation found for systematic {}!".format(syst))
            continue

        envelop = {}
        for key, var in variations.items():
            nominal = f.Get(key)

            env = getEnvelopHistograms(nominal, var)
            env[0].SetName(nominal.GetName() + "__{}up".format(syst))
            env[1].SetName(nominal.GetName() + "__{}down".format(syst))

            envelop[key] = env
        envelopes.append(envelop)

    # Re-open the file in write mode
    f.Close()
    f = ROOT.TFile.Open(input, "update")

    for envelop in envelopes:
        for key, env in envelop.items():
            env[0].Write('', ROOT.TObject.kOverwrite)
            env[1].Write('', ROOT.TObject.kOverwrite)

    f.Close()

