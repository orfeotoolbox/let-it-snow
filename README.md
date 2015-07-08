## Synopsis

todo

## Code Example

todo

## Motivation

todo

## Installation

to configure on venus calc:

source /mnt/data/home/otbtest/config_otb.sh
cd $build_dir
cmake -DCMAKE_CXX_FLAGS:STRING=-std=c++11 -DCMAKE_CXX_COMPILER:FILEPATH=/usr/bin/g++-4.8 -DCMAKE_C_COMPILER:FILEPATH=/usr/bin/gcc-4.8 -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON $source_dir
make

## API Reference

## Tests

## Contributors

## License


