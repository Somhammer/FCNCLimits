#! /bin/bash
# Run fit
text2workspace.py ttbb_Discriminant_bb_2D_dRvsM.dat -m 173 -o ttbb_Discriminant_bb_2D_dRvsM_combine_workspace.root -P HiggsAnalysis.CombinedLimit.ttbbFitModel:ttbbFitModel --PO ttbj=627.96 --PO ttbb=724.66 --PO ttbkg=188.99 --PO data_obs=2499.0 --PO other=168.82 --PO ttcc=72.11 --PO qcd=198.37 --PO ttLF=490.38 
combine -M MultiDimFit --algo grid --points 50 ttbb_Discriminant_bb_2D_dRvsM_combine_workspace.root -m 125 -n nominal
plot1DScan.py higgsCombinenominal.MultiDimFit.mH125.root --POI r_bbbj --output bbbj_scan
plot1DScan.py higgsCombinenominal.MultiDimFit.mH125.root --POI r_tt --output tt_scan
plot1DScan.py higgsCombinenominal.MultiDimFit.mH125.root --POI r_qcd --output qcd_scan

#combine -M MultiDimFit --algo grid --points 50 ttbb_Discriminant_bb_2D_dRvsM_combine_workspace.root --snapshotName MultiDimFit --freezeNuisances all 

#PostFitShapesFromWorkspace -w ttbb_Discriminant_bb_2D_dRvsM_combine_workspace.root -d ttbb_Discriminant_bb_2D_dRvsM.dat -o postfit_shapes_ttbb_Discriminant_bb_2D_dRvsM.root -f fitDiagnostics_ttbb_Discriminant_bb_2D_dRvsM_postfit.root:fit_s --postfit --sampling
#python ../../convertPostfitShapesForPlotIt.py -i postfit_shapes_ttbb_Discriminant_bb_2D_dRvsM.root
#$CMSSW_BASE/src/UserCode/plotIt/plotIt -o postfit_shapes_ttbb_Discriminant_bb_2D_dRvsM_forPlotIt ../../config_forPlotIt/postfit_plotIt_config_ttbb_2016_bb_2D_dRvsM.yml -y
    
