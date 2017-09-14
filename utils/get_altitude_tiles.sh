#!/bin/bash
p="/work/OT/muscate/prod/muscate_prod/data_production/dataref/"
echo "Tile Mean_Altitude_Over_L2_Coverage Altitude_Standard_Deviation_Over_L2_Coverage" > Altitude_Over_L2_Coverage.txt
for i in `ls -d $p/S2__TEST_AUX_REFDE2_T*`
do
t=`basename $i | cut -d_ -f6`
ma=`grep -i Mean_Altitude_Over_L2_Coverage $p/S2*$t*/S2*$t*/S2*$t*.HDR | cut -d\> -f2 | cut -d\< -f1 `
as=`grep -i Altitude_Standard_Deviation_Over_L2_Coverage $p/S2*$t*/S2*$t*/S2*$t*.HDR | cut -d\> -f2 | cut -d\< -f1 `
echo $t $ma $as >> Altitude_Over_L2_Coverage.txt
done
