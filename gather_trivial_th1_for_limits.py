import ROOT
import os

base_dir = '/home2/minerva1993/HEPToolsFCNC/fullAna/doReco/2017/STFCNC01/post_process'
#base_dir = '/home2/minerva1993/HEPToolsFCNC/fullAna/doReco/2018/STFCNC01/post_process'
base_output_dir = 'histos_suitable_for_limits_200101_2017_trivial/'
#base_output_dir = 'histos_suitable_for_limits_200101_2018_trivial/'

if not os.path.isdir(base_output_dir):
    os.mkdir(base_output_dir)

# NB assumes DNN is in name of TH!

coupling_strings = ['Hct', 'Hut']
systematics_in_separated_rootfiles = ['hdamp', 'jec', 'jer', 'TuneCP5'] # first entry for the rootfiles with nominal and other syst TH1

# Derive first the list of processes
rootfile_dir = base_dir
process_list = [process.split('.')[0] for process in os.listdir(rootfile_dir) if process.endswith('.root') and not '__' in process]
print 'Found following rootfiles : ', process_list

output_dir = os.path.join(base_output_dir)
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)
for process in process_list:
    output_file_name = os.path.join(output_dir, process + '.root')
    print "Writing %s"%output_file_name
    output_rootfile = ROOT.TFile(output_file_name, 'recreate')
    for coupling_string in coupling_strings:
        rootfile_path = os.path.join(rootfile_dir, process + '.root')
        rootfile = ROOT.TFile(rootfile_path)
        output_rootfile.cd()
        for th1_key in rootfile.GetListOfKeys():
            th1_name = th1_key.GetName()
            if not 'h_LepPt_Ch' in th1_name: continue
            if not any(i in th1_name for i in ['S2','S3','S6','S7','S8']): continue
            th1 = rootfile.Get(th1_name)
            if 'Ch0' in th1_name: ch_string = 'Ch0'
            elif 'Ch1' in th1_name: ch_string = 'Ch1'
            elif 'Ch2' in th1_name: ch_string = 'Ch2'
            if 'S2' in th1_name: jet_string = 'j3b2'
            elif 'S3' in th1_name: jet_string = 'j3b3'
            elif 'S6' in th1_name: jet_string = 'j4b2'
            elif 'S7' in th1_name: jet_string = 'j4b3'
            elif 'S8' in th1_name: jet_string = 'j4b4'

            if '__' in th1_name:
                new_th1_name = coupling_string + '_h_DNN_' + jet_string + '_' + ch_string + '__' + str(th1_name.split('__')[1])
            else: new_th1_name = coupling_string + '_h_DNN_' + jet_string + '_' + ch_string
            th1.SetName(new_th1_name)
            th1.Write()
            del th1
        rootfile.Close()

        for syst in systematics_in_separated_rootfiles:
            for var in ['up', 'down']:
                rootfile_path = os.path.join(rootfile_dir, process + '__' + syst + var + '.root')
                rootfile = ROOT.TFile(rootfile_path)
                output_rootfile.cd()
                for th1_key in rootfile.GetListOfKeys():
                    th1_name = th1_key.GetName()
                    th1_name = th1_key.GetName()
                    if not 'h_LepPt_Ch' in th1_name: continue
                    if not any(i in th1_name for i in ['S2','S3','S6','S7','S8']): continue
                    th1 = rootfile.Get(th1_name)
                    if 'Ch0' in th1_name: ch_string = 'Ch0'
                    elif 'Ch1' in th1_name: ch_string = 'Ch1'
                    elif 'Ch2' in th1_name: ch_string = 'Ch2'
                    if 'S2' in th1_name: jet_string = 'j3b2'
                    elif 'S3' in th1_name: jet_string = 'j3b3'
                    elif 'S6' in th1_name: jet_string = 'j4b2'
                    elif 'S7' in th1_name: jet_string = 'j4b3'
                    elif 'S8' in th1_name: jet_string = 'j4b4'
                    new_th1_name = coupling_string + '_h_DNN_' + jet_string + '_' + ch_string
                    th1.SetName(new_th1_name)
                    th1.Write()
                rootfile.Close()
    output_rootfile.Close()

