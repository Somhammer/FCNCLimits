strDataCard = """\
imax %(binnum)i
jmax %(procnum)i
kmax *
--------------------------------------------------------------------------------
shapes * * %(input_root)s $PROCESS_$CHANNEL $PROCESS_$CHANNEL__$SYSTEMATIC
--------------------------------------------------------------------------------
bin %(bins)s
observation %(observations)s
--------------------------------------------------------------------------------
bin %(listBin)s
process %(listProc)s
process %(listProcIdx)s
rate %(listNmc)s
--------------------------------------------------------------------------------
%(listSys)s
--------------------------------------------------------------------------------
%(rateParamMC)s
%(rateParamUnfold)s
%(paramMC)s
%(regularization)s
%(sysGroup)s
"""

strTextToWorkspace = """\
text2workspace.py {datacard} -m 125 -o {workspace} -P {model} {pois}
"""
#HiggsAnalysis.CombinedLimit.PhysicsModel:multiSignalModel

strCombine = """\
combine {workspace} -n {outname} -m 125 {options}\
"""

strScanRegularizationScript = """\
basePath=$CMSSW_BASE/src/UserCode/ttbbDiffXsec
arrayDelta=$(python $basePath/compute{minimize}.py 1 {minDelta} {maxDelta} {points}) 
for testDelta in ${{arrayDelta[@]}} 
do
  {combine} --setParameters delta=$testDelta
  python compute{minimize}.py 2 multidimfit{outname}.root {minimize}.root $testDelta
done
bestDelta=$(python $basePath/computeGCC.py 3 {minimize}.root)
echo "Best delta: " $bestDelta
"""
#format(minDelta=minDelta,maxDelta=maxDelta,points=points, combineOptions=combineOptions)

strToyTestTemplate = """\
{combine} -t -1
python $CMSSW_BASE/src/HiggsAnalysis/CombinedLimit/test/diffNuisances.py -a fitDiagnostics_{name}_bkgPlusSig.root -g fitDiagnostics_{name}_bkgPlusSig_plots.root > fitDiagnostics_{name}_bkgPlusSig.log
python $CMSSW_BASE/src/UserCode/ttbbDiffXsec/printPulls.py fitDiagnostics_{name}_bkgPlusSig_plots.root
#print NLL for check
#combineTool.py -M FastScan -w {name}_combine_workspace.root:w -o {name}_nll
"""

strImpactTemplate = """\
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --doInitialFit --robustFit=1 --robustHesse 1 -t -1
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 --robustFit=1 --robustHesse 1 --doFits -t -1 --parallel 32
combineTool.py -M Impacts -d {name}_combine_workspace.root -m 125 -o {name}_expected_impacts.json -t -1
arrayPOIs = {pois}
for poi in ${{arrayPOIs[@]}}
do
  plotImpacts.py -i {name}_expected_impacts.json -o {name}_impacts_$poi --po $poi --per-page 40
done

combineTools.py -M Impacts -d {name}_combine_workspace.root -m 125 --doInitialFit --robustFit=1 --robustHesse 1
combineTools.py -M Impacts -d {name}_combine_workspace.root -m 125 --robustFit=1 --robustHesse 1 --doFits --parallel 32
combineTools.py -M Impacts -d {name}_combine_workspace.root -m 125 -o {name}_impacts.json
arrayPOIs = {pois}
for poi in ${{arrayPOIs[@]}} 
do
  plotImpacts.py -i {name}_impacts.json -o {name}_impacts_$poi --po $poi --per-page 40
done
"""

strPlottingBestFit = """\
python $CMSSW_BASE/src/UserCode/makePostFitPlotsForPlotIt.py -d={discriminantName} -h={hist} -i=multidimfit_{name}_postfit.root -o=post_shapes_{name}_forPlotIt -y={year} -l={lumi} 
$CMSSW_BASE/src/UserCode/plotIt/plotIt -o post_spahes_{name}_forPlotIt $CMSSW_BASE/src/UserCode/configs/postfit_plotIt_config_{discriminantName}.yml -y
"""
#format(name=output_prefix, discriminantName=discriminantName, hist=histName, year=options.dataYear[-2:], lumi=options.luminosity)

strUncertaintyBreakdown = """\
bestDelta=$(python ../../computeGCC.py 3 gcc.root)

combine {name}_combine_workspace.root -M MultiDimFit --algo none -m 125 --setParameters delta=$bestDelta -n Bestfit --saveWorkspace
combine higgsCombineBestfit.MultiDimFit.mH125.root -M MultiDimFit --algo grid --points 1000 -m 125 --setParameters delta=$bestDelta -n Nominal 

combine higgsCombineBestfit.MultiDimFit.mH125.root -M MultiDimFit --algo grid --points 1000 -m 125 --setParameters delta=$bestDelta -n Theory --freezeNuisanceGroups theory
combine higgsCombineBestfit.MultiDimFit.mH125.root -M MultiDimFit --algo grid --points 1000 -m 125 --setParameters delta=$bestDelta -n TheorySyst --freezeNuisanceGroups theory syst 
combine higgsCombineBestfit.MultiDimFit.mH125.root -M MultiDimFit --algo grid --points 1000 -m 125 --setParameters delta=$bestDelta -n StatOnly --freezeNuisanceGroups allConstrainedNuisances 
combine higgsCombineBestfit.MultiDimFit.mH125.root -M MultiDimFit --algo grid --points 1000 -m 125 --setParameters delta=$bestDelta -n All --freezeParameters all

arrayPOI={pois}
for poi in ${{arrayPOI[@]}}
do
  plot1DScan.py higgsCombineNominal.MultiDimFit.mH125.root --output totalUncertainty
  plot1DScan.py higgsCombineNominal.MultiDimFit.mH125.root --others 'higgsCombineTheory.MultiDimFit.mH125.root:Freeze th.:4' 'higgsCombineTheorySyst.MultiDimFit.mH125.root:Freeze th. sy.:3' --breakdown theory,syst,stat --output breakdownUncertainties_TheorySystStat
done

arraySyst={syst}
for syst in ${{arraySyst[@]}}
do
  echo "Systematic: " $syst
  combine higgsCombineBestfit.MultiDimFit.mH125.root -M MultiDimFit --algo grid --points 1000 -m 125 --setParameters delta=$bestDelta -n $syst --freezeParameters $syst
  for poi in ${{arrayPOI[@]}} 
  do
    plot1DScan.py higgsCombineNominal.MultiDimFit.mH125.root --others 'higgsCombine$syst.MultiDimFit.mH125.root:Freeze $syst:4' --POI $poi --breakdown $syst,other --output $poi\_$syst
  done
done
"""
