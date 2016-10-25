#!/bin/bash

export MODULEPATH=$MODULEPATH:/work/logiciels/modulefiles/		

module purge

module load cmake/3.0.2
module load gcc
module load boost
module load otb/5.6
module load python/2.7.5

pkg="lis"
version="cloudremoval"
name=$pkg-$version
src=$DATACI/modules/repository/$name/lis
install_dir=$DATACI/modules/repository/$name/$name-install
log=$DATACI/modules/repository/$name/build.log
data_root=$DATACI/modules/repository/$name/Data-LIS

echo "Building $pkg version $version ..."

# clean previous build
rm -rf $install_dir/*
rm $log

mkdir -p $install_dir
cd $install_dir

#setup ENV for testing
export PATH=$install_dir/bin:$PATH
export LD_LIBRARY_PATH=$install_dir/bin:$LD_LIBRARY_PATH
export PYTHONPATH=$install_dir/bin:$install_dir/bin/lib/python2.7/site-packages:$PYTHONPATH

echo "Configuring ..."
CC=$GCCHOME/bin/gcc CXX=$GCCHOME/bin/g++ cmake -DBUILD_TESTING=ON -DLIS_DATA_ROOT=$data_root -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER:STRING=$CC -DCMAKE_CXX_COMPILER:STRING=$CXX -DCMAKE_CXX_FLAGS="-std=c++11" -DPYTHON_LIBRARY=${PYTHONHOME}/lib -DPYTHON_INCLUDE_DIR=${PYTHONHOME}/include/python2.7 -DGDAL_INCLUDE_DIR=/work/logiciels/otb/5.2.1/include $src &>> $log

echo "Building ..."
make -j2 &>> $log

cd $install_dir/python
python setup.py install -f --prefix $install_dir/bin

#add install_dir to qtis linux group and appropriate rights
chmod -R 755 $install_dir
chmod -R 755 $data_root

echo "Launch LIS tests ..."
cd $install_dir
ctest -VV &>> $log

echo "Done. Check $log for build details."
