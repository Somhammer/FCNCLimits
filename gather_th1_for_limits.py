import ROOT
import os

base_dir = '/home/minerva1993/HEPToolsFCNC/finalMVA/histos/2017/'
#base_dir = '/home/minerva1993/HEPToolsFCNC/finalMVA/histos/2018/'
base_output_dir = 'histos_suitable_for_limits_191014_2017/'
#base_output_dir = 'histos_suitable_for_limits_190910_2018_v10/'

if not os.path.isdir(base_output_dir):
    os.mkdir(base_output_dir)

# NB assumes DNN is in name of TH!

coupling_strings = ['Hct', 'Hut']
#jet_strings = ['j3', 'j4']
jet_strings = ['j3b2', 'j3b3', 'j4b2', 'j4b3', 'j4b4']
#training_strings = ['01', '02', '03', '04']
training_strings = ['0101010101'] #ver of j3b2+j3b3+j4b2+j4b3+j4b4

systematics_in_separated_rootfiles = ['hdamp', 'jec', 'jer', 'TuneCP5'] # first entry for the rootfiles with nominal and other syst TH1

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
            for th1_key in rootfile.GetListOfKeys():
                th1_name = th1_key.GetName()
                if not 'DNN' in th1_name:
                    continue
                th1 = rootfile.Get(th1_name)
                #new_th1_name = coupling_string + '_' + jet_string + '_' + th1_name
                new_th1_name = coupling_string + '_' + th1_name
                th1.SetName(new_th1_name)
                th1.Write()
            rootfile.Close()
            for syst in systematics_in_separated_rootfiles:
                for var in ['up', 'down']:
                    rootfile_path = os.path.join(rootfile_dir, process + '__' + syst + var + '.root')
                    rootfile = ROOT.TFile(rootfile_path)
                    output_rootfile.cd()
                    for th1_key in rootfile.GetListOfKeys():
                        th1_name = th1_key.GetName()
                        if not 'DNN' in th1_name:
                            continue
                        th1 = rootfile.Get(th1_name)
                        #new_th1_name = coupling_string + '_' + jet_string + '_' + th1_name + '__' + syst + var
                        new_th1_name = coupling_string + '_' + th1_name + '__' + syst + var
                        th1.SetName(new_th1_name)
                        th1.Write()
                    rootfile.Close()
        output_rootfile.Close()

