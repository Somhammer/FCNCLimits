import ROOT
import os, re

base_dir = '/home2/minerva1993/HEPToolsFCNC/finalMVA/histos/2017/'
#base_dir = '/home2/minerva1993/HEPToolsFCNC/finalMVA/histos/2018/'
base_output_dir = 'histos_suitable_for_limits_200101v15_2017/'
#base_output_dir = 'histos_suitable_for_limits_200101v2_2018/'

if not os.path.isdir(base_output_dir):
    os.mkdir(base_output_dir)

# NB assumes DNN is in name of TH!

coupling_strings = ['Hct', 'Hut']
#jet_strings = ['j3', 'j4']
jet_strings = ['j3b2', 'j3b3', 'j4b2', 'j4b3', 'j4b4']
#training_strings = ['01', '02', '03', '04']
training_strings = ['0101010101'] #ver of j3b2+j3b3+j4b2+j4b3+j4b4

systematics_in_separated_rootfiles = ['hdamp', 'jec', 'jer', 'TuneCP5'] # first entry for the rootfiles with nominal and other syst TH1
systematics_to_merge = {'lepton':'(\S*)__(el|mu)(\S*)',}#'btag':'(\S*)__(lf|hf|cferr)(\S*)'}

# Derive first the list of processes
#rootfile_dir = os.path.join(base_dir, coupling_strings[0] + "_" + jet_strings[0] + '_' + training_strings[0], 'post_process')
rootfile_dir = os.path.join(base_dir, coupling_strings[0] + '_' + training_strings[0], 'post_process')
process_list = [process.split('.')[0] for process in os.listdir(rootfile_dir) if process.endswith('.root') and not '__' in process]
print 'Found following rootfiles : ', process_list

for training_string in training_strings:
    output_dir = os.path.join(base_output_dir, 'training_'+training_string)
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
    for process in process_list:
        output_file_name = os.path.join(output_dir, process + '.root')
        print "Writing %s"%output_file_name
        output_rootfile = ROOT.TFile(output_file_name, 'recreate')
        for coupling_string in coupling_strings:
            #for jet_string in jet_strings:
            #folder_name = coupling_string + "_" + jet_string + '_' + training_string
            folder_name = coupling_string + "_" + training_string
            rootfile_dir = os.path.join(base_dir, folder_name, 'post_process')
            rootfile_path = os.path.join(rootfile_dir, process + '.root')
            rootfile = ROOT.TFile(rootfile_path)
            output_rootfile.cd()

            # Store median and up/down template with 0 content/error
            median_dist = {}
            for th1_key in rootfile.GetListOfKeys():
                th1_name = th1_key.GetName()
                if not 'j3b2' in th1_name: continue
                if not 'DNN' in th1_name: continue
                if '__' in th1_name: continue
                th1 = rootfile.Get(th1_name)
                th1a = rootfile.Get(th1_name.replace('j3b2','j3b3'))
                th1b = rootfile.Get(th1_name.replace('j3b2','j4b2'))
                th1c = rootfile.Get(th1_name.replace('j3b2','j4b3'))
                th1d = rootfile.Get(th1_name.replace('j3b2','j4b4'))
                th1.Add(th1a,1.0)
                th1.Add(th1b,1.0)
                th1.Add(th1c,1.0)
                th1.Add(th1d,1.0)
                #new_th1_name = coupling_string + '_' + jet_string + '_' + th1_name
                new_th1_name = coupling_string + '_' + th1_name
                th1.SetName(new_th1_name)

                for key in systematics_to_merge.keys():
                    median_dist[new_th1_name + '__' + key] = [th1]
                    th1_up = th1.Clone(new_th1_name + '__' + key + 'up')
                    th1_down = th1.Clone(new_th1_name + '__' + key + 'down')
                    th1_up.Add(th1, -1)
                    th1_down.Add(th1, -1)
                    for n in xrange(1, th1.GetNbinsX()+1):
                        th1_up.SetBinError(n,0) #set to 0
                        th1_down.SetBinError(n,0)
                    #th1_up.Sumw2() #already done
                    #th1_down.Sumw2()
                    median_dist[new_th1_name + '__' + key].extend([th1_up,th1_down])
            #print median_dist

            for th1_key in rootfile.GetListOfKeys():
                th1_name = th1_key.GetName()
                if not 'j3b2' in th1_name: continue
                if not 'DNN' in th1_name: continue
                th1 = rootfile.Get(th1_name)
                th1a = rootfile.Get(th1_name.replace('j3b2','j3b3'))
                th1b = rootfile.Get(th1_name.replace('j3b2','j4b2'))
                th1c = rootfile.Get(th1_name.replace('j3b2','j4b3'))
                th1d = rootfile.Get(th1_name.replace('j3b2','j4b4'))
                th1.Add(th1a,1.0)
                th1.Add(th1b,1.0)
                th1.Add(th1c,1.0)
                th1.Add(th1d,1.0)
                #new_th1_name = coupling_string + '_' + jet_string + '_' + th1_name
                new_th1_name = coupling_string + '_' + th1_name
                th1.SetName(new_th1_name)

                if not any(re.compile(i, re.IGNORECASE).search(new_th1_name) for i in systematics_to_merge.values()):
                    th1.Write()
                else:
                    for key, val in systematics_to_merge.items():
                        if re.compile(val, re.IGNORECASE).search(new_th1_name):
                            hist_key = str(new_th1_name.split('__')[0]) + '__' + key
                            if 'up' in new_th1_name:
                                th1.Add(median_dist[hist_key][0], -1)
                                median_dist[hist_key][1].Add(th1)
                            elif 'down' in new_th1_name:
                                th1.Add(median_dist[hist_key][0], -1)
                                median_dist[hist_key][2].Add(th1)

            # Store up/down histograms
            for val in median_dist.values():
                h_up = val[1]
                h_dn = val[2]
                h_up.Add(val[0], 1)
                h_dn.Add(val[0], 1)
                h_up.Write()
                h_dn.Write()

            rootfile.Close()

            for syst in systematics_in_separated_rootfiles:
                for var in ['up', 'down']:
                    rootfile_path = os.path.join(rootfile_dir, process + '__' + syst + var + '.root')
                    rootfile = ROOT.TFile(rootfile_path)
                    output_rootfile.cd()
                    for th1_key in rootfile.GetListOfKeys():
                        th1_name = th1_key.GetName()
                        if not 'j3b2' in th1_name: continue
                        if not 'DNN' in th1_name: continue
                        th1 = rootfile.Get(th1_name)
                        th1a = rootfile.Get(th1_name.replace('j3b2','j3b3'))
                        th1b = rootfile.Get(th1_name.replace('j3b2','j4b2'))
                        th1c = rootfile.Get(th1_name.replace('j3b2','j4b3'))
                        th1d = rootfile.Get(th1_name.replace('j3b2','j4b4'))
                        th1.Add(th1a,1.0)
                        th1.Add(th1b,1.0)
                        th1.Add(th1c,1.0)
                        th1.Add(th1d,1.0)
                        #new_th1_name = coupling_string + '_' + jet_string + '_' + th1_name + '__' + syst + var
                        new_th1_name = coupling_string + '_' + th1_name + '__' + syst + var
                        th1.SetName(new_th1_name)
                        th1.Write()
                    rootfile.Close()
        output_rootfile.Close()

