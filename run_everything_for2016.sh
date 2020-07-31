datacardFolder=$1 
python prepareShapesAndCards.py -p $CMSSW_BASE/src/UserCode/tHFCNC/Limit/FinalFits/suitable_for_prepareShapeAndCards_200101/ -dataYear 2016 -l 1 -le 1.025 -xsecfile xsec_2016.yml -rebinning 1 -o $datacardFolder #--sysToAvoid jec hdamp scale lepton pdf pu TuneCP5
#python prepareShapesAndCards.py -p $CMSSW_BASE/src/UserCode/tHFCNC/Limit/FinalFits/suitable_for_prepareShapeAndCards_200101/ -dataYear 2016 -l 1 -le 1.025 -xsecfile xsec_2016_TOP-17-003.yml -rebinning 1 -o $datacardFolder --sysToAvoid jec hdamp scale lepton pdf pu TuneCP5 #Reproducing 2016 paper
#python prepareShapesAndCards.py -p $CMSSW_BASE/src/UserCode/tHFCNC/Limit/FinalFits/suitable_for_prepareShapeAndCards_200101/ -dataYear 2016 -l 1 -le 1.025 -xsecfile xsec_2016.yml -rebinning 99 -o $datacardFolder #--sysToAvoid jec hdamp scale lepton pdf pu TuneCP5 #Rebin by significance
python run_all_limits.py $datacardFolder
python plotLimitsPerCategory.py -lumi 35.9 -limitfolder $datacardFolder
python printLimitLatexTable.py $datacardFolder False
python run_all_closureChecks.py $datacardFolder
python run_all_impacts.py $datacardFolder
python run_all_gatherFailedFits.py $datacardFolder
python run_all_postfits.py $datacardFolder
