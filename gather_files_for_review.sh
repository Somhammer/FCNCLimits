datacard16=$1
datacard17=$2
datacard18=$3
datacardRun2=$4
outname=$5

mkdir $outname

declare -a FolderList=($datacard16 $datacard17 $datacard18 $datacardRun2)
for folder in "${FolderList[@]}"
do
  mkdir $outname/$folder
  mkdir $outname/$folder/Hut
  mkdir $outname/$folder/Hct

  cp $folder/Hut/*.dat $outname/$folder/Hut
  cp $folder/Hct/*.dat $outname/$folder/Hct
  cp $folder/Hut/*shapes.root $outname/$folder/Hut
  cp $folder/Hct/*shapes.root $outname/$folder/Hct
  cp $folder/Hut/forCombine*.root $outname/$folder/Hut
  cp $folder/Hct/forCombine*.root $outname/$folder/Hct
done
