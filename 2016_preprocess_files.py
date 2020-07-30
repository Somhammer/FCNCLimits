import ROOT, os
# script that runs over the rootfile used for 2016 analysis and translate them to our format. It also removes the cross section (and factor 0.1) scaling applied to signals (this way the normalization for 2016 signal will also be 1 pb as we have for 2017 and 2018)
# NB: lumi rescaling is already applied to the 2016 TH1, it has to be set to 1 in prepareShapesAndCards

cmssw_base = os.environ['CMSSW_BASE']
rootfile_path = cmssw_base + '/src/UserCode/tHFCNC/Limit/FinalFits/merged/'
rescaled_rootfile_path = cmssw_base + '/src/UserCode/tHFCNC/Limit/FinalFits/suitable_for_prepareShapeAndCards/' # for the output rootfiles
if not os.path.exists(cmssw_base + '/src/UserCode/tHFCNC/Limit/FinalFits/suitable_for_prepareShapeAndCards/'):
  os.makedirs(cmssw_base + '/src/UserCode/tHFCNC/Limit/FinalFits/suitable_for_prepareShapeAndCards/')
# input_MVAHutComb_b4j4_hut.root
Xsec_2016 = {'Hut': {"ST":13.8, "TT": 37.0}, 'Hct': {"ST":1.90, "TT":37.0}}
extra_factor_2016 = 10  #No need to un-apply the extra factor 1.36 since we use here the signal TH1 splitted for ST and TT while this 1.36 was only applied to the TH1 corresponding to their sum ('sig')
# the ttbar signal NNLO reweighting will be applied in xsec.yml (by giving it more weight w.r.t. ST)
list_2016_processName = ["data_obs", "sig_stop_Hct", "sig_ttbar_Hct", "sig_stop_Hut", "sig_ttbar_Hut", "ttbb", "ttcc", "ttlf", "other"]
rootfile_2016_list = ['input_MVAHctComb_b2j3_hct.root', 'input_MVAHctComb_b3j3_hct.root', 'input_MVAHctComb_b4j4_hct.root', 'input_MVAHutComb_b2j4_hut.root', 'input_MVAHutComb_b3j4_hut.root', 'input_MVAHctComb_b2j4_hct.root', 'input_MVAHctComb_b3j4_hct.root', 'input_MVAHutComb_b2j3_hut.root', 'input_MVAHutComb_b3j3_hut.root', 'input_MVAHutComb_b4j4_hut.root']

systematics_list_from_datacard_2016_2017 = {'Jes':'jec', 'hdamp':'hdamp', 'scaleEnvelope':'scale', 'SfIteraviveFitHfstats1':'hfstat1', 'SfIteraviveFitHfstats2':'hfstat2', 'SfIteraviveFitLfstats1':'lfstat1', 'SfIteraviveFitLfstats2':'lfstat2', 'SfIteraviveFitLf':'lf', 'SfIteraviveFitHf':'hf', 'SfIteraviveFitCferr1':'cferr1', 'SfIteraviveFitCferr2':'cferr2', 'Jer':'jer'} # Additional systematics are stored in the rootfile but were not used for limit setting (they are not in the 2016 datacards). This list ensures we only store the systematics that were actually used
for process in list_2016_processName:
    processInTh1 = process.replace("_Hct","").replace("_Hut","")
    print "Treating %s"%process
    rootfile_output = ROOT.TFile(os.path.join(rescaled_rootfile_path, process+".root"), 'recreate')
    for rootfile_name in rootfile_2016_list:
        rootfile = ROOT.TFile(os.path.join(rootfile_path, rootfile_name))
        for th1_key in rootfile.GetListOfKeys():
            if (th1_key.GetName().startswith("combSTandTT_"+processInTh1+"_") and not 'StatBin' in th1_key.GetName()) or th1_key.GetName() == "combSTandTT_"+processInTh1:
                th1 = ROOT.TH1F(rootfile.Get(th1_key.GetName()))
                Hct_or_Hut = ""
                if 'hct.root' in rootfile_name:
                    Hct_or_Hut = "Hct"
                elif 'hut.root' in rootfile_name:
                    Hct_or_Hut = "Hut"
                jet_bin_str = ""
                if "b2j3" in rootfile_name:
                    jet_bin_str = "j3b2"
                elif "b3j3" in rootfile_name:
                    jet_bin_str = "j3b3"
                elif "b2j4" in rootfile_name:
                    jet_bin_str = "j4b2"
                elif "b3j4" in rootfile_name:
                    jet_bin_str = "j4b3"
                elif "b4j4" in rootfile_name:
                    jet_bin_str = "j4b4"
                #th1_new_name = Hct_or_Hut + "_" + jet_bin_str + "_h_DNN_b" + jet_bin_str[-1] + "_Ch2"  
                th1_new_name = Hct_or_Hut + "_h_DNN_" + jet_bin_str + "_Ch2"  
                if th1_key.GetName()[-2:] == "Up":
                    if th1_key.GetName().split("_")[-1][:-2] not in systematics_list_from_datacard_2016_2017.keys():
                        continue
                    th1_new_name += "__" + th1_key.GetName().split("_")[-1]
                    th1_new_name = th1_new_name[:-2] + "up"
                    th1_new_name = th1_new_name.replace(th1_key.GetName().split("_")[-1][:-2], systematics_list_from_datacard_2016_2017[th1_key.GetName().split("_")[-1][:-2]])
                elif th1_key.GetName()[-4:] == "Down":
                    if th1_key.GetName().split("_")[-1][:-4] not in systematics_list_from_datacard_2016_2017.keys():
                        continue
                    th1_new_name += "__" + th1_key.GetName().split("_")[-1]
                    th1_new_name = th1_new_name[:-4] + "down"
                    th1_new_name = th1_new_name.replace(th1_key.GetName().split("_")[-1][:-4], systematics_list_from_datacard_2016_2017[th1_key.GetName().split("_")[-1][:-4]])
                th1.SetName(th1_new_name)
                if processInTh1 == 'sig_stop':
                    cross_section = Xsec_2016[Hct_or_Hut]["ST"]
                    th1.Scale(extra_factor_2016/cross_section)
                elif processInTh1 == 'sig_ttbar':
                    cross_section = Xsec_2016[Hct_or_Hut]["TT"]
                    th1.Scale(extra_factor_2016/cross_section)
                rootfile_output.cd()
                th1.Write()
                rootfile.cd()
    rootfile_output.Close()
    print os.path.join(rescaled_rootfile_path, process+".root"), " written."




#for rootfile_name in os.listdir(rootfile_path):
#    list_of_ttbar_th1 = []
#    rootfile_rescaled = ROOT.TFile(os.path.join(rescaled_rootfile_path, rootfile_name), 'recreate')
#    rootfile = ROOT.TFile(os.path.join(rootfile_path, rootfile_name))
#    for th1_key in rootfile.GetListOfKeys():
#        #print rootfile.Get(th1_key.GetName())
#        th1 = ROOT.TH1F(rootfile.Get(th1_key.GetName()))
#        #th1 = rootfile.Get(th1_key.GetName())
#        if '_sig_ttbar' in th1_key.GetName():
#            th1.Scale(1.23)
#            list_of_ttbar_th1.append(th1_key.GetName())
#        rootfile_rescaled.cd()
#        th1.Write()
#        rootfile.cd()
#    rootfile.Close()
#    rootfile_rescaled.cd()
#    for ttbar_th1_name in list_of_ttbar_th1:
#        if 'StatBinSig' in ttbar_th1_name:
#            continue
#        stop_th1_name = ttbar_th1_name.replace('_sig_ttbar','_sig_stop')
#        sum_th1_name = ttbar_th1_name.replace('_sig_ttbar','_sig')
#        stop_th1 = ROOT.TH1F(rootfile_rescaled.Get(stop_th1_name))
#        ttbar_th1 = ROOT.TH1F(rootfile_rescaled.Get(ttbar_th1_name))
#        sum_th1 = ROOT.TH1F(rootfile_rescaled.Get(sum_th1_name))
#        sum_yield = sum_th1.Integral()
#        sum_th1 = stop_th1.Clone()
#        sum_th1.Add(ttbar_th1)
#        tmp_integral = sum_th1.Integral()
#        sum_th1.Scale(sum_yield/sum_th1.Integral())
#        print "Old integral: ", sum_yield, " Tmp integral: ", tmp_integral, "New integral: ", sum_th1.Integral()
#        sum_th1.Write()
#    rootfile_rescaled.Close()
#    print os.path.join(rescaled_rootfile_path, rootfile_name), " written."

