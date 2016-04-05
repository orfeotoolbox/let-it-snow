#/bin/sh

# Path to the SRTM virtual raster dataset
fsrtm="/mnt/data/DONNEES_AUX/SRTM/srtm.vrt"

# Path to images
pimg="/mnt/data/home/gascoins/Landsat8"

# Tiles to process
tiles="N2A_France-MetropoleD0005H0001 N2A_France-MetropoleD0005H0002"

# Path to write the output DEM
pout="/mnt/data/home/gascoins/Landsat8/SRTM"

# Full extent images from Level2
for s0 in $tiles
do
 
  # input folder to get target image SRS and extent
  p="$pimg/$s0"

  # only one file is needed to get the SRS
  f=$(ls $p/*/*PENTE*TIF | head -n1)

  # get target extent
  # gdal_warp convention = xmin ymin xmax ymax
  xminymin=$(gdalinfo $f | grep "Lower Left" | tr -d '(,)A-z' | awk '{print $1, $2}')
  xmaxymax=$(gdalinfo $f | grep "Upper Right" | tr -d '(,)A-z' | awk '{print $1, $2}')
  te="$xminymin $xmaxymax"

  # get the SRS
  proj=$(gdalsrsinfo -o proj4 $f | tr -d "'")

  # output folder to write projected SRTM
  po="$pout/$s0/"
  mkdir -p $po

  # projet SRTM dem with cubicspline resampling (target resolution in 20 m x 20 m) 
  gdalwarp -dstnodata -32768 -tr 30 30 -r cubicspline -overwrite -te $te -t_srs "$proj" $fsrtm $po$s0.tif &

done
wait
exit 0

