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
import templateCollection as tc

def write_datacard_for_unfold(self, output, discriminant, regularization):
    print "Writing datacard for %s..." % discriminant
    
    listColGen  = []
    listColData = []
    listColProc = []
    listRateParamSig = []
    listRateParamBkg = []
    listParamBkg = []
    listPoi = []
    pois = []

    strSigRateParamTemplate = "%s rateParam * %s* %lf [0.0,%lf]"
    strBkgRateParamTemplate = "%s rateParam %s %s 1.0 [0.0,10.0]"
    strBkgParamTemplate = "%s param 1.0 0.3"

    root_input = ROOT.TFile.Open(self.output_filename)
    root_input.cd()
    bkgIdx = 1
    sigIdx = 0
    categories = [n.GetName() for n in root_input.GetListOfKeys()]
    for signal in self.signals:
        output_prefix = '%s_Discriminant_%s' % (signal, discriminant)
        if not os.path.exists(os.path.join(output, signal)):
            os.makedirs(os.path.join(output, signal))
        datacard = os.path.join(os.path.join(output, signal, output_prefix + '.dat'))
        root_output = ROOT.TFile(os.path.join(output, signal, output_prefix + '_shapes.root'), 'recreate')
        root_output.cd()
        for bin in categories:
            TH1 = root_input.Get(bin+'/data_obs')
            TH1.SetName('data_obs_'+bin)
            TH1.Write()
            listColData.append({'bin':bin,'obs':TH1.Integral()})
            root_dir = root_input.Get(bin)
            processes = [n.GetName() for n in root_dir.GetListOfKeys() if signal in n.GetName() and not '__' in n.GetName()]
            for idx, proc in enumerate(processes):
                poi = 'unfold_'+str(idx+1)
                pois.append(poi)
                outname = proc+'_'+bin+'_'+bin
                TH1 = root_input.Get(bin+'/'+proc)
                TH1.SetName(outname)
                TH1.Write()
                rate = TH1.Integral()

                tmp = []
                for systematic in self.systematics:
                    variations = ['Up','Down']
                    for vari in variations:
                        TH1 = root_input.Get(bin+'/'+proc+'__'+systematic+vari)
                        TH1.SetName(outname+'__'+systematic+vari)
                        TH1.Write()
                    tmp.append('1')
                
                    #listColGen.append({'bin':ibin,'poi':strGen,'nevt':nevt})
                    #listRateParamSig.append(strSigRateParamTemplate % (strGen, signal+'_gen'+str(ibin), 1.0, 10.0))
                listColProc.append({'bin':bin,'proc':proc+'_'+bin,'procIdx':sigIdx,'rate':rate,'syst':tmp})
               
                sigIdx -= 1
            for background in self.backgrounds:
                poi = background 
                outname = background+'_'+bin+'_'+bin
                TH1 = root_input.Get(bin+'/'+background)
                TH1.SetName(outname)
                TH1.Write()
                rate = TH1.Integral()

                tmp = []
                if 'qcd' in background:
                    for i in range(len(self.systematics)): tmp.append('-')
                else:
                    for systematic in self.systematics:
                        if any(i == systematic for i in [ut.CMSNamingConvention(self.year, s, self.correlate_syst) for s in self.syst_for_tt]) and not background in self.ttbkg:
                            tmp.append('-')
                        else:
                            variations = ['Up','Down']
                            for vari in variations:
                                TH1 = root_input.Get(bin+'/'+background+'__'+systematic+vari)
                                TH1.SetName(outname+'__'+systematic+vari)
                                TH1.Write()
                            tmp.append('1')
                listColProc.append({'bin':bin,'proc':background+'_'+bin,'procIdx':bkgIdx,'rate':rate,'syst':tmp})
                #listRateParamBkg.append(strBkgRateParamTemplate % (procName, disc[1], procName,))
                #listParamBkg.append(strBkgParamTemplate % (procName))
                bkgIdx += 1

    tmp = set(listPoi)
    listPoi = list(tmp)
    listRegularization = []
    tmp = set(pois)
    pois = list(tmp)

    # Regularization
    ### Singular vector decomposition
    if regularization['mode'].lower() == "svd":
        strRegTemplate = "constr{idx} constr {binLo}-2*{binMed}+{binHi} {delta}"
        strRegEdgeTemplate = "constr{idx} constr {binLo}-{binHi} {delta}"

        listRegularization.append(strRegEdgeTemplate.format(
            idx = 0, delta = regularization['delta'],
            binLo = pois[0],
            binHi = pois[1]))

        for ibin in range(1, len(pois)-1):
            listRegularization.append(strRegTemplate.format(
                idx = ibin, delta = regularization['delta'],
                binLo = pois[ibin-1],
                binMed = pois[ibin],
                binHi = pois[ibin+1]))

        listRegularization.append(strRegEdgeTemplate.format(
            idx = len(pois)-1, delta = regularization['delta'],
            binLo = pois[-2],
            binHi = pois[-1]))

    ### Tikhonov regularization (TUnfold regularization)
    ### NEED TO UPDATE
    elif regularization['mode'].lower() == "tikhonov":
        strRegTemplate = "constr{idx} constr {binLo}-2*{binMed}+{binHi} {{{params}}} {delta}"
        strBinTemplate = "({bin}-1.0)*({shapeSum})"
        strShapeTemplate = "shape_ttbb_{genBin}_{recoBin}__norm"

        def getBinSum(ibin, params):
            shapes = []
            for jbin in range(len(discriminant)):
                norm = strShapeTemplate.format(
                    genBin = 'gen'+str(ibin),
                    recoBin = discriminant[jbin][1])
            shapes.append(norm)
            params.append(norm)

            binSum = strBinTemplate.format(
                bin = listColGen[ibin]['poi'],
                shapeSum = '+'.join(shapes))

            params.append(listColGen[ibin]['poi'])

            return binSum

        for ibin in range(1, len(listColGen)-1):
            params = []
            binLo  = getBinSum(ibin-1, params)
            binMed = getBinSum(ibin,   params)
            binHi  = getBinSum(ibin+1, params) 

            listRegularization.append(strRegTemplate.format(
                idx = ibin, delta = config['regularization']['delta'],
                params = ','.join(list(sorted(set(params)))),
                binLo = binLo, binMed = binMed, binHi = binHi))

    #print "Regularization Formula: ", '\n'.join(reg for reg in listRegularization)
    listSyst = []
    listTheory = []
    listExp = []
    
    listSyst.append('CMS_%s_lumi lnN ' % (self.year) + (str(self.luminosityError) + ' ') * len(listColProc))
    for idx, value in enumerate(self.systematics):
        if any(i == value for i in [ut.CMSNamingConvention(self.year, s, self.correlate_syst) for s in ['sw','tune','ps','pdf','hdamp']]):
            listTheory.append(value)
        else:
            listExp.append(value)
        strSyst = value + ' shape'
        for item in listColProc:
            strSyst += ' '+item['syst'][idx]
        listSyst.append(strSyst)
    listExp.append('CMS_%s_lumi' % self.year)
    #print "Theory: ", listTheory
    #print "Experiment: ", listExp
    strTheory = 'theory group = '+' '.join(item for item in listTheory)
    strExp    = 'syst group = '+' '.join(item for item in listExp)
    strSysGroup = strTheory +'\n' + strExp

    dictIn = {}
    dictIn['input_root'] = str(os.path.basename(os.path.join(output, signal, output_prefix + '_shapes.root')))
    dictIn['binnum'] = len(discriminant)
    dictIn['procnum'] = len(listColProc) - 1 
    dictIn['bins'] = ' '.join(d['bin'] for d in listColData)
    dictIn['observations'] = ' '.join(str(d['obs']) for d in listColData)
    dictIn['listBin'] = ' '.join(d['bin'] for d in listColProc)
    dictIn['listProc'] = ' '.join(d['proc'] for d in listColProc)
    dictIn['listProcIdx'] = ' '.join(str(d['procIdx']) for d in listColProc)
    dictIn['listNmc'] = ' '.join(str(d['rate']) for d in listColProc)
    dictIn['listSys'] = '\n'.join(item for item in listSyst)
    dictIn['rateParamMC'] = ''#'\n'.join(item for item in listRateParamBkg)
    dictIn['rateParamUnfold'] = ''#'\n'.join(item for item in listRateParamSig)
    dictIn['paramMC'] = ''#'\n'.join(item for item in listParamBkg)
    dictIn['regularization'] = '\n'.join(item for item in listRegularization)
    dictIn['sysGroup'] = strSysGroup 

    strCardContent = tc.strDataCard % dictIn
    with open(datacard, 'w') as fCard: fCard.write(strCardContent)

    print "Done. Datacard saved as %r" % datacard
    return datacard, pois

def write_datacard_by_harvester(self, output, discriminant):
    print "Writing datacard for %s..." % discriminant
    
    root_input = ROOT.TFile.Open(self.output_filename)
    import CombineHarvester.CombineTools.ch as ch
    for signal in self.signals:
        mc_categories = self.backgrounds + [signal]
        output_prefix = '%s_Discriminant_%s' % (signal, discriminant)
        datacard = os.path.join(os.path.join(output, signal, output_prefix + '.dat'))
        cb = ch.CombineHarvester()
        cb.AddObservations(['*'],[''],['_%s'%self.year],[''],discriminant)
        cb.AddProcesses(['*'],[''],['_%s'%self.year],[''],self.backgrounds,discriminant,False)
        cb.AddProcesses(['*'],[''],['_%s'%self.year],[''],[signal],discriminant,True)
        if not options.nosys:
            cb.cp().AddSyst(cb, 'CMS$ERA_lumi', 'lnN', ch.SystMap()(self.luminosityError))
            for systematic in self.systematics:
                systematic_only_for_SMtt = False
                for systSMtt in self.syst_for_tt:
                    if CMSNamingConvention(systSMtt) == systematic:
                        systematic_only_for_SMtt = True
                if not systematic_only_for_SMtt:
                    cb.cp().AddSyst(cb, systematic, 'shape', ch.SystMap('process')([x for x in mc_categories if not 'qcd' in x], 1.00))
                else:
                    cb.cp().AddSyst(cb, systematic, 'shape', ch.SystMap('process')(self.ttbkg, 1.00))
        cb.cp().backgrounds().ExtractShapes(file, '$BIN/$PROCESS', '$BIN/$PROCESS__$SYSTEMATIC')
        cb.cp().signals().ExtractShapes(file, '$BIN/$PROCESS', '$BIN/$PROCESS__$SYSTEMATIC')
        cb.cp().WriteDatacard(datacard, root_input)

    print "Done. Datacard saved as %r" % datacard
