datacardFolder=$1
year=$2
runQCD=${3:false}
qcdFile=${4:-"hist_dataDriven_QCD"}
lumi=([16]=35922 [17]=41529 [18]=59741)
lumiErr=([16]=1.025 [17]=1.023 [18]=1.025)

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
      python run_scripts.py ${datacardFolder}_${val} make_workspace 
      python run_scripts.py ${datacardFolder}_${val} run_postfits
      for syst in ${systematics[@]}; do
        python prepareShapesAndCards.py -p hists/root${year}_qcd -dataYear 20${year} -l ${lumi[$year]} -le ${lumiErr[$year]} -xsecfile xsec_txt/files${year}_qcd.yml -o ${datacardFolder}_${val}${syst} -s S2 -c $val -q $runQCD -qi ${qcdFile}${syst}.root
        python run_scripts.py ${datacardFolder}_${val}${syst} make_workspace 
        python run_scripts.py ${datacardFolder}_${val}${syst} run_postfits
      done
    done
  else
    echo "Fit and unfold"
    python main.py -p hists/root${year}_post -y ${year} -l ${lumi[$year]} -le ${lumiErr[$year]} --config configs/combine${year}.yml --xsecfile configs/files${year}.yml -o $datacardFolder -c Ch2 -s S7
    python run_scripts.py $datacardFolder make_workspace
    python run_scripts.py $datacardFolder scan_regparams 
    python run_scripts.py $datacardFolder run_toytest
    python run_scripts.py $datacardFolder run_postfits
    python run_scripts.py $datacardFolder run_impacts
    python run_scripts.py $datacardFolder run_breakdown
  fi
fi
#python printLimitLatexTable.py $datacardFolder False

