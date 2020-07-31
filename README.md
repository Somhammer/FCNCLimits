# FCNCLimits
Toolbox to derive upper limits for 2017/2018 FCNC tH(bb) analysis
# Installation
```
export SCRAM_ARCH=slc6_amd64_gcc530
cmsrel CMSSW_8_1_0
cd CMSSW_8_1_0/src 
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v7.0.11
cd -
git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
cd CombineHarvester
git checkout 3573c4e14931a9ca9b7557ddf3fe85cf56383df8
cd -
mkdir UserCode
git clone https://github.com/BrieucF/FCNCLimits UserCode/FCNCLimits
scram build clean; scram build --ignore-arch
```
# Stay up to date
You can check that the above recipe is up to date by following the links
https://cms-hcomb.gitbooks.io/combine/content/part1/#for-end-users-that-dont-need-to-commit-or-do-any-development
and
http://cms-analysis.github.io/CombineHarvester/index.html#getting-started

# Run the limits
If not done earlier (now we do it before limit setting step), extract envelope of the systematics for which it is necessary

`python makeEnvelope.py -p /path/to/your/rootfiles`

Write the datacards and rootfiles suitable for combine (be careful that cross sections and sum of event weights are taken from `xsec.yml` and that for signal cross section is different than the one used in `plotIt`!)

`python prepareShapesAndCards.py -p /path/to/your/rootfiles`

Run combine to extract the limits

`python run_all_limits.py`

Plot the limits and print the values extrapolated to branching ratios

`python plotLimitsPerCategory.py`

All these python scripts are easily configurable, check what you can do with the `--help` option

To see how to do postfit plots, nuisance pulls, impacts, etc, have a look at the file: `run_everything_for2018.sh`

You can also print limits in form of latex table with `printLimitLatexTable.py`

# To pay attention to

The signal cross section you use in 'xsec.yml' has to be propagated to `plotLimitsPerCategory.py` and to `printLimitLatexTable.py`. Note that `plotLimitsPerCategory.py` also needs the real, physical, expected signal cross section (for coupling one) to derive the limit on branching ratio.

# Script documentation

Script by script explanation (some might be slightly outdated or need minor modifications to adapt to different data taking year)

`2016_compute_limit.sh` derives limits using out of the box 2016 datacards. Make sure you wrote right path for root files

`2016_get_real_exclLim_and_br.py` transforms the limit obtained from out of the box 2016 datacards into physical limits (taking into account the normalization used to obtain signal yields in these datacards)

`2016_preprocess_files.py` in view of combination of 2017+2018 analyses with existing 2016, some homogenization is required (align the systematics name, the background definitions, the signal cross sections used and the rootfile format). This script just re-process the 2016 rootfile to make them compliant for `prepareShapesAndCards.py`. Not validated yet.

`convertPostfitShapesForPlotIt.py` makes the output of `combine` suitable for plotIt when deriving post-fit plots

`gather_th1_for_limits.py` pre-process 2017 and 2018 TH1 to make them suitable for `prepareShapesAndCards.py` (e.g. gather jec TH1 which are in separatred rootfiles into the same rootfile than other systematics)

`histos_postfit_Hc(u)t.yml` plotIt yml histogram configuration file for Hc(u)t post-fit plot

`list_histo.py` script for debugging, useful e.g. to check the presence (or absence) of a given TH1 inside a rootfile containing hundreads of them

`makeEnvelope.py` for systematics with more than just up/down variation (e.g. scale or pdf), one has to derive to envelope to have well defined up/down shape. This script computes this envelope and store it in the rootfile. Currently not needed anymore because this step is done earlier in the chain.

`plotLimitsPerCategory.py` stores limit values inside a json file and makes the plot with limits on signal cross section per jet category and with all jet categories combined

`postfit_file_Hc(u)t.yml` plotIt yml process configuration file for Hc(u)t post-fit plot

`postfit_plotIt_config_Hc(u)t_2017(8).yml` plotIt yml global configuration file for Hc(u)t post-fit plot in 2017(8)

`prepareShapesAndCards.py` based on the TH1 obtained from `gather_th1_for_limits.py`, writes datacards and rootfiles to feed combine (taking care of systematics, rescaling to lumi*Xsec/Nevent, etc). This code also writes several bash script to derive the limits with combine, perform the pre-approval checks (pulls and impact of systematics), post-fit shapes, ...

`printLimitLatexTable.py` print a latex pre-formatted table with limits taken from the json file produced by `plotLimitsPerCategory.py`

`printPulls.py` when you run the closure checks (e.g. from the bash script written by `prepareShapesAndCards.py`) information about pulls is stored in a rootfile by combine, this script just prints the pull plot in png format

`run_all_closureChecks.py`, `run_all_impacts.py`, `run_all_limits.py`, `run_all_postfits.py` scripts used to automatize the full chain. It launches the various combine commands in the bash scripts written by `prepareShapesAndCards.py`

`run_everything_for2016/7/8.sh` **THE** script launching everything you need: writing datacards, producing limits on signal cross section, plot them, print a latex table with them, run closure checks of the pulls. derive impact plot and postfit plots

`run_withoutPrepCard.sh` same then `run_everything_for2016/7/8.sh` but without the datacard writing part

`setTDRStyle.C` used to be compliant with CMS style guidelines (used in `plotLimitsPerCategory.py`)

All the `xsec.yml` contain the cross section and number of generated events used by `prepareShapesAndCards.py` to apply proper normalization before limit setting

`update_an.sh` script used to automatize the update of the AN after generating new limits (writes the latex table with limits in the AN, change the limits and psotfit plots, etc). It has to be updated to whatever format will be decided for AN combining 2017 and 2018.

#Run 2 combination
`run_everything_for161718.sh` read datacards defined as `-p16/17/17` and generate output folder with merged datacards. Then run limit, pull, impact in the directory
`correlateUnc.py` changes fully correlated sources across the year to partially correlated sources. For example, to excute the code for JEC, `python ../../correlateUnc.py FCNC_Hct_Discriminant_DNN_Hct_161718_all.dat --process CMS_jec,0.5,2017-2018  --output-txt test_datacard.txt --output-root test_datacard.root` in the datacard folder. In the process option, argument carries source name, correlation and years. Years are divided by '-', so if you want to include 2016 as well, type `2016-2017-2018`. The output card and new root file with histograms will be generated.

#Customization for closure check label
'./path_to/HiggsAnalysis/CombinedLimit/test/diffNuisances.py', add 'hist_prefit.LabelsOption("v")' before draw

