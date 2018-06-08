# Run Let It Snow from MAJA


This tutorial will presents how to run the LIS algorithm (Let It Snow) to
produce Snow surface products from the output of the 

## Run MAJA

The MAJA processor (MACCS ATCOR Joint Algorithm, say "maya") is the state of the
art for cloud detection and atmospheric correction, specifically designed to
process time series of optical images at high resolution, acquired under quasi
constant viewing angles. It allows for instance to process time series of
LANDSAT or Sentinel-2 images.

The delivered version of MAJA can ingest L1 products int the following formats
(delivered in the package):

- Sentinel-2: (PSD) S2-PDGS-TAS-DI-PSD  v.12 AND v.14.2
- Landsat8: Landsat8_Level1_Data_Format_Control_Book_LSDS-809
- Landsat 5-7: CNES internal format described in PSC-IF-411-0081-CNES_E1R4

MAJA is the processor used on `theia <http://www.theia-land.fr/>`_, to produce
Surface Reflance products.       

For more information about how to download and run MAJA check `here
<https://logiciels.cnes.fr/en/content/maja>`_.

With MAJA, you will need to generate DEM tile to

This input will also used as input of LIS.

We'll process a tile near Mount Artos in Turkey

## Generate LIS JSON parameters using build_json.py script

MAJA outputs consists in a directory with

In my case, I have a directory called:


```
S2A_OPER_SSC_L2VALD_38SLH____20180311.DBL.DIR

```
with the surface reflectances and could mask provided as GeoTiff.

And the DTM generates prepare_mnt tool available here : http://tully.ups-tlse.fr/olivier/prepare_mnt 

We're going to use the utilities script build_json.py to configure LIS and generate.


