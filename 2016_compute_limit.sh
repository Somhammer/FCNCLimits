# The signal yields in 2016 datacards have been divided by 10 --> to get the proper limit you should multiply by Xsec/10, Kirill was using Hut=50.82 and Hct=38.88 pb
# Rootfile path from git repo are not the correct one (from strasbourg cluster), need to change them to
# /user/kskovpen/analysis/Limit/CMSSW_7_4_7/src/Limit/merge/merged/input_MVAHutComb_b3j3_hut.root --> /afs/cern.ch/user/b/brfranco/work/public/FCNC/limits/CMSSW_8_1_0/src/UserCode/tHFCNC/Limit/FinalFits/merged/input_MVAHutComb_b3j3_hut.root

cd $CMSSW_BASE/src/UserCode/tHFCNC/Limit/FinalFits/cards
combine -M AsymptoticLimits -d comb_MVAHutComb_hut.txt -S 1 --run expected
#combine -M AsymptoticLimits -d comb_MVAHctComb_hct.txt -S 1 --run expected
cd -
