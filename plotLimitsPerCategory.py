import os, sys, argparse, json
import ROOT

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1', 'True'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0', 'False'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

parser = argparse.ArgumentParser(description='Store limits inside a json file and plot them if required (one bin per category).')
parser.add_argument('-limitfolder', dest='limitfolder', default='./datacards', type=str, help='Folder where Hct and Hut combine output folders are stored')
parser.add_argument('-verbose', dest='verbose', type=bool, default=False, help='Dump limits to stdout or not.')
parser.add_argument('-doPlot', dest='doPlot', type=str2bool, default="True", help='Do the limit plot or not.')
parser.add_argument('-category_order', dest='category_order', nargs='+', default=['b2j3', 'b2j4', 'b3j3', 'b3j4', 'b4j4', 'all'], help='Bin order in the limit plot, names must be the same then in the combine rootfile: e.g. higgsCombine*_b3j3*.root.')
parser.add_argument('-bin_labels', dest='category_labels', nargs='+', default=['b2j3', 'b2j4', 'b3j3', 'b3j4', 'b4j4', 'all'], help='Use this option if you want to modify the x-axis labels. Must be same order and length then -category_order argument.')
parser.add_argument('-unblind', dest='unblind', type=bool, default=False, help='Display or not the observed limit.')
parser.add_argument('-lumi', dest='lumi', type=str, default='41.5', help='Luminosity to display on the plot.')
parser.add_argument('-removeHutb4j4', dest='removeHutb4j4', type=str2bool, default="False", help='Remove Hut b4j4 from plots')
parser.add_argument('-printlimits', dest='printlimits', type=str2bool, default="False", help='Print b2j3 and b2j4 to check run2 combination')

options = parser.parse_args()
if options.printlimits:
    options.category_order = ['161718_all', '1617_all', '1718_all']

ROOT.gROOT.SetBatch()

#limit on branching ratio: Excluded limit --> excluded coupling: sigXsecDivK2 = 47.68, sigXsecDivK2 * Khqt^2 <  XsecEcl --> Khqt^2 < XsecExcl/sigXsecDivK2
#    Excluded couping ---> ExcBr: BR(t --> Hq) = Width(t --> Hq)* Khqt^2/TotalWidth = 0.19*Khqt^2/1.32158
#    <--> BR(t --> Hq) < XsecExcl*0.19/(sigXsecDivK2 * 1.32158)

signal_Xsec_couplingOne = {"Hut": 1, "Hct": 1}  # for limit rescaling if the signal Xsec inseted in combine was not 1 pb
#signal_Xsec_couplingOne = {"Hut": 1.527, "Hct": 1.527}  # for limit rescaling if the signal Xsec inseted in combine was not 1 pb
signal_Xsec_couplingOneForBR = {"Hut": 60.34, "Hct": 48.4} # to extract limit on BR: BR(t --> Hq) < XsecExcl*Width(t-->Hq)/(sigXsec * TotalWidth) = XsecExcl*0.19/(sigXsec * 1.32158)
#signal_Xsec_couplingOneForBR = {'Hut': 50.82, 'Hct': 38.88} # to extract limit on BR: BR(t --> Hq) < XsecExcl*Width(t-->Hq)/(sigXsec * TotalWidth) = XsecExcl*0.19/(sigXsec * 1.32158)

def getLimitsFromFile(input_file):
    """
    Extract observed, expected, and 1/2 sigma limits from combine output rootfile
    """
    f = ROOT.TFile.Open(input_file)
    if not f or f.IsZombie() or f.TestBit(ROOT.TFile.kRecovered):
        return None

    data = {}
    # Index 0 is DOWN error, index 1 is UP error
    one_sigma = data.setdefault('one_sigma', [0, 0])
    two_sigma = data.setdefault('two_sigma', [0, 0])

    limit = f.Get('limit')

    limit.GetEntry(2)
    data['expected'] = limit.limit

    limit.GetEntry(5)
    data['observed'] = limit.limit

    limit.GetEntry(4)
    two_sigma[1] = limit.limit
    #two_sigma[1] = limit.limit - data['expected']

    limit.GetEntry(0)
    #two_sigma[0] = data['expected'] - limit.limit
    two_sigma[0] = limit.limit

    limit.GetEntry(3)
    #one_sigma[1] = limit.limit - data['expected']
    one_sigma[1] = limit.limit

    limit.GetEntry(1)
    #one_sigma[0] = data['expected'] - limit.limit
    one_sigma[0] = limit.limit

    return data

def add_labels(canvas, additional_label='', lumi=options.lumi, energy='13', cms='Work in progress'):
    latexLabel = ROOT.TLatex()
    latexLabel.SetTextSize(0.75 * canvas.GetTopMargin())
    latexLabel.SetNDC()
    latexLabel.SetTextFont(42) # helvetica
    latexLabel.DrawLatex(0.69, 0.96, lumi + ' fb^{-1} (%s TeV)'%energy)
    latexLabel.SetTextFont(61) # helvetica bold face
    latexLabel.SetTextSize(1.15 * canvas.GetTopMargin())
    latexLabel.DrawLatex(0.78, 0.85, additional_label)
    latexLabel.SetTextSize(0.75 * canvas.GetTopMargin())
    latexLabel.DrawLatex(0.13, 0.96, "CMS")
    latexLabel.SetTextFont(52) # helvetica italics
    latexLabel.DrawLatex(0.22, 0.96, cms)


def plot_limits(signal_name, limit_dict, legend_position=[0.2, 0.7, 0.65, 0.9]):
    cat_order = options.category_order[:] #copy by value not to modify original options
    cat_label = options.category_labels[:]
    if options.removeHutb4j4 and signal_name == 'Hut':
      cat_order.remove('b4j4')
      cat_label.remove('b4j4')
    nBins = len(limit_dict)
    bin_low_edges = array('d', range(nBins+1))
    #canvas = ROOT.TCanvas(signal_name + "_limits_per_category", signal_name + "_limits_per_category", 600, 450)
    canvas = ROOT.TCanvas(signal_name + "_limits_per_category", signal_name + "_limits_per_category")
    th1_for_canvas_layout = ROOT.TH1F("bla", "bla", nBins, bin_low_edges)
    th1_for_canvas_layout.SetLineColorAlpha(ROOT.kWhite, 0)
    xAxis = th1_for_canvas_layout.GetXaxis()
    xAxis.CenterLabels()
    xAxis.SetLabelSize(0.07)
    xAxis.SetLabelFont(42)
    xAxis.SetTitleFont(42)
    xAxis.SetTitleFont(42)
    yAxis = th1_for_canvas_layout.GetYaxis()
    #yAxis.SetNdivisions(010)
    yAxis.SetTitle("95% CL upper limit on #sigma #times BR [pb]")
    yAxis.SetLabelFont(42)
    yAxis.SetTitleFont(42)
    yAxis.SetTitleSize(0.039)
    expected_lines = {}
    observed_lines = {}
    one_sigma_rectangles = {}
    two_sigma_rectangles = {}
    for category_binNumber in range(len(cat_order)):
        category = cat_order[category_binNumber]
        if category in limit_dict.keys():
            categ_limits = limit_dict[category]
            xAxis.SetBinLabel(category_binNumber+1, cat_label[category_binNumber])
            th1_for_canvas_layout.SetBinContent(category_binNumber+1, categ_limits['two_sigma'][1]*1.5)
    th1_for_canvas_layout.SetMinimum(0)
    th1_for_canvas_layout.Draw()
    for category_binNumber in range(len(cat_order)):
        category = cat_order[category_binNumber]
        if category in limit_dict.keys():
            categ_limits = limit_dict[category]
            xlow = xAxis.GetBinLowEdge(category_binNumber+1)
            xup = xAxis.GetBinUpEdge(category_binNumber+1)
            one_sigma_up = categ_limits['one_sigma'][1]
            one_sigma_down = categ_limits['one_sigma'][0]
            two_sigma_up = categ_limits['two_sigma'][1]
            two_sigma_down = categ_limits['two_sigma'][0]
            expected_lines[category] = ROOT.TLine(xlow, categ_limits['expected'], xup, categ_limits['expected'])
            expected_lines[category].SetLineStyle(7)
            expected_lines[category].SetLineWidth(2)
            observed_lines[category] = ROOT.TLine(xlow, categ_limits['observed'], xup, categ_limits['observed'])
            observed_lines[category].SetLineWidth(2)
            if not options.unblind:
                observed_lines[category].SetLineColorAlpha(ROOT.kWhite, 0)
            one_sigma_rectangles[category] = ROOT.TPolyLine(4, array('d', [xlow, xup, xup, xlow]), array('d',[one_sigma_down, one_sigma_down, one_sigma_up, one_sigma_up] ))
            one_sigma_rectangles[category].SetFillColor(3)
            one_sigma_rectangles[category].SetLineColor(3)
            #one_sigma_rectangles[category].SetFillStyle(3001)
            two_sigma_rectangles[category] = ROOT.TPolyLine(4, array('d', [xlow, xup, xup, xlow]), array('d',[two_sigma_down, two_sigma_down, two_sigma_up, two_sigma_up] ))
            two_sigma_rectangles[category].SetFillColor(5)
            two_sigma_rectangles[category].SetLineColor(5)
            #two_sigma_rectangles[category].SetFillStyle(3001)
            two_sigma_rectangles[category].Draw('f same')
            one_sigma_rectangles[category].Draw('f same')
            expected_lines[category].Draw('same')
            observed_lines[category].Draw('same')
    # Legend
    legend = ROOT.TLegend(legend_position[0], legend_position[1], legend_position[2], legend_position[3], "95% CL upper limits")
    legend.SetTextFont(42)
    legend.SetFillStyle(0)
    legend.SetFillColor(ROOT.kWhite)
    legend.SetLineColor(ROOT.kWhite)
    legend.SetShadowColor(ROOT.kWhite)
    legend.AddEntry(expected_lines[limit_dict.keys()[0]], 'Expected', 'l')
    legend.AddEntry(one_sigma_rectangles[limit_dict.keys()[0]], 'Expected #pm 1 std. deviation', 'f')
    legend.AddEntry(two_sigma_rectangles[limit_dict.keys()[0]], 'Expected #pm 2 std. deviations', 'f')
    legend.AddEntry(observed_lines[limit_dict.keys()[0]], 'Observed', 'l')
    legend.Draw('same')
    add_labels(canvas, signal_name)
    th1_for_canvas_layout.Draw('sameaxis')#reprint ticks on top of rectangles
    canvas.Print(os.path.join(options.limitfolder, signal_name + '_limits.pdf'))
    canvas.Print(os.path.join(options.limitfolder, signal_name + '_limits.png'))
    #canvas.SetLogy()
    #canvas.Print(os.path.join(options.limitfolder, signal_name + '_limits_log.pdf'))
    #canvas.Print(os.path.join(options.limitfolder, signal_name + '_limits_log.png'))
    if options.printlimits:
      print "Limit on Xsec for %s 161718_all jet cat: %f"%(signal_name, limit_dict['161718_all']['expected'])
      print "Limit on BR for %s 161718_all jet cat: %f %%"%(signal_name, 100*limit_dict['161718_all']['expected']*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s 161718_all jet cat one sigma up: %f %%"%(signal_name, 100*limit_dict['161718_all']['one_sigma'][1]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s 161718_all jet cat one sigma down: %f %%"%(signal_name, 100*limit_dict['161718_all']['one_sigma'][0]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))

      print "Limit on Xsec for %s 1617_all jet cat: %f"%(signal_name, limit_dict['1617_all']['expected'])
      print "Limit on BR for %s 1617_all jet cat: %f %%"%(signal_name, 100*limit_dict['1617_all']['expected']*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s 1617_all jet cat one sigma up: %f %%"%(signal_name, 100*limit_dict['1617_all']['one_sigma'][1]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s 1617_all jet cat one sigma down: %f %%"%(signal_name, 100*limit_dict['1617_all']['one_sigma'][0]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))

      print "Limit on Xsec for %s 1718_all jet cat: %f"%(signal_name, limit_dict['1718_all']['expected'])
      print "Limit on BR for %s 1718_all jet cat: %f %%"%(signal_name, 100*limit_dict['1718_all']['expected']*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s 1718_all jet cat one sigma up: %f %%"%(signal_name, 100*limit_dict['1718_all']['one_sigma'][1]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s 1718_all jet cat one sigma down: %f %%"%(signal_name, 100*limit_dict['1718_all']['one_sigma'][0]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))

    else:
      print "Limit on Xsec for %s all jet cat: %f"%(signal_name, limit_dict['all']['expected'])
      print "Limit on BR for %s all jet cat: %f %%"%(signal_name, 100*limit_dict['all']['expected']*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s all jet cat one sigma up: %f %%"%(signal_name, 100*limit_dict['all']['one_sigma'][1]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))
      print "Limit on BR for %s all jet cat one sigma down: %f %%"%(signal_name, 100*limit_dict['all']['one_sigma'][0]*0.19/(signal_Xsec_couplingOneForBR[signal_name]*1.32158))

signal_folders = [folder for folder in os.listdir(options.limitfolder) if os.path.isdir(os.path.join(options.limitfolder, folder))]
if not signal_folders:
    print "Found no folder inside %s"%options.limitfolder
    sys.exit(1)

for signal_folder in signal_folders:
    print "Extracting limits for %s"%signal_folder
    signal_folder_path = os.path.join(options.limitfolder, signal_folder)
    limit_rootfiles = [rootfile for rootfile in os.listdir(signal_folder_path) if rootfile.startswith('higgsCombineFCNC')]
    #categories = [] # [rootfilename.split('.')[0].split('_')[-1] for rootfilename in limit_rootfiles]
    dict_cat_limits = {}
    for category in options.category_order:
        found_category = False
        if options.removeHutb4j4 and 'Hut/' in signal_folder_path and category == 'b4j4': continue
        for limit_rootfile in limit_rootfiles:
            limit_rootfile_path = os.path.join(signal_folder_path, limit_rootfile)

            #special treat for full  run2
            if options.printlimits: category_tmp = limit_rootfile.split('.')[0].split('_')[-2] + '_' + 'all'
            else: category_tmp = limit_rootfile.split('.')[0].split('_')[-1]

            if category_tmp == category:
                if found_category:
                    print "Error: two rootfiles match category name %s in %s, don't know which one to choose. Please move one of them."%(category, signal_folder_path)
                    sys.exit(1)
                found_category = True
                limits = getLimitsFromFile(limit_rootfile_path)
                for number_type in limits:
                    if isinstance(limits[number_type], list):
                        limits[number_type][0] = limits[number_type][0]*signal_Xsec_couplingOne[signal_folder]
                        limits[number_type][1] = limits[number_type][1]*signal_Xsec_couplingOne[signal_folder]
                    else:
                        limits[number_type] = limits[number_type]*signal_Xsec_couplingOne[signal_folder]
                dict_cat_limits[category] = limits
        if not found_category:
            print "Warning: I do not find rootfile for category %s in %s. The code assumes rootfile name of the form e.g. higgsCombine*_b3j3*.root without underscore after category name."%(category, signal_folder_path)
    json_limit_filepath = os.path.join(options.limitfolder, signal_folder + '_limits.json')
    if options.verbose:
        print json.dumps(dict_cat_limits, indent=4)
    with open(json_limit_filepath, 'w') as limit_json:
        json.dump(dict_cat_limits, limit_json)
    print "%s written with limits inside"%json_limit_filepath

    if options.doPlot:
        from array import array
        ROOT.gROOT.ProcessLine(".x setTDRStyle.C")
        plot_limits(signal_folder, dict_cat_limits)
