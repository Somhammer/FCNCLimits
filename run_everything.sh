datacardFolder=$1
year=$2
runQCD=${3:false}
qcdFile=${4:-"hist_dataDriven_QCD"}
lumi=([16]=35922 [17]=41529 [18]=59741)
lumiErr=([16]=1.025 [17]=1.023 [18]=1.025)
avoidSyst=([16]="prefire" [17]="" [18]="prefire")

if [ "$#" -lt 1 ]; then
  echo "$# is Illegal number of parameters. Please set the year and datacardFolder"
  echo "Usage: $0 [datacardFolder] [year] [runQCD] [qcdFile]"
  exit 1
else
  if [ $runQCD ]; then
    echo "Estimate QCD scale factor"
    channels=("mu" "el")
    systematics=("__qcdisoup" "__qcdisodown")
    for val in ${channels[@]}; do
      python prepareShapesAndCards.py -p hists/root${year}_qcd -dataYear 20${year} -l ${lumi[$year]} -le ${lumiErr[$year]} -xsecfile xsec_txt/files${year}_qcd.yml -o ${datacardFolder}_${val} -s S2 -c $val -q $runQCD -qi ${qcdFile}.root
      python run_all_postfits.py ${datacardFolder}_${val}
      #python run_all_closureChecks.py ${datacardFolder}_${val}
      #python run_all_impacts.py ${datacardFolder}_${val}
      for syst in ${systematics[@]}; do
        python prepareShapesAndCards.py -p hists/root${year}_qcd -dataYear 20${year} -l ${lumi[$year]} -le ${lumiErr[$year]} -xsecfile xsec_txt/files${year}_qcd.yml -o ${datacardFolder}_${val}${syst} -s S2 -c $val -q $runQCD -qi ${qcdFile}${syst}.root
        python run_all_postfits.py ${datacardFolder}_${val}${syst}
        #python run_all_closureChecks.py ${datacardFolder}_${val}${syst}
        #python run_all_impacts.py ${datacardFolder}_${val}${syst}
      done
    done
  else
    echo "Fit and unfold"
    if [ $year -eq 17 ]; then
      python prepareShapesAndCards.py -p hists/root${year}_post -dataYear 20${year} -l ${lumi[$year]} -le ${lumiErr[$year]} -xsecfile xsec_txt/files${year}.yml -o $datacardFolder -s S3 
    else
      python prepareShapesAndCards.py -p hists/root${year}_post -dataYear 20${year} -l ${lumi[$year]} -le ${lumiErr[$year]} -xsecfile xsec_txt/files${year}.yml -o $datacardFolder -s S3 --sysToAvoid ${avoidSyst[$year]} 
    fi
    python run_scripts.py $datacardFolder run_postfits
    #python run_all_closureChecks.py $datacardFolder run_closureChecks
    #python run_scripts.py $datacardFolder run_impacts
  fi
fi

#python plotLimitsPerCategory.py -lumi 35.9 -limitfolder $datacardFolder -removeHutb4j4 False
#python printLimitLatexTable.py $datacardFolder False

