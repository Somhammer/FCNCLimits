datacardFolder=$1
python prepareShapesAndCards.py -p histos_suitable_for_limits_200101v34_2018/training_0101010101/ -dataYear 2018 -l 59741 -le 1.025 -xsecfile xsec_2018_200101.yml --sysToAvoid prefire elzvtx -o $datacardFolder
python run_all_limits.py $datacardFolder
python plotLimitsPerCategory.py -lumi 59.7 -limitfolder $datacardFolder
python printLimitLatexTable.py $datacardFolder False
python run_all_closureChecks.py $datacardFolder
python run_all_impacts.py $datacardFolder
python run_all_gatherFailedFits.py $datacardFolder
python run_all_postfits.py $datacardFolder
