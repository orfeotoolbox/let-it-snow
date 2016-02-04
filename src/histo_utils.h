/*=========================================================================

  Program:   lis
  Language:  C++

  Copyright (c) Simon Gascoin
  Copyright (c) Manuel Grizonnet

  See lis-copyright.txt for details.

  This software is distributed WITHOUT ANY WARRANTY; without even
  the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
  PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#ifndef HISTO_UTILS_H
#define HISTO_UTILS_H

#include <string>
#include "itkVectorImage.h"
#include "itkImageToHistogramFilter.h"

int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim);
int compute_snow_fraction(const std::string & infname);

short compute_zs_ng(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim, const char * histo_file=NULL);

short compute_zs_ng_internal(const itk::VectorImage<short, 2>::Pointer compose_image, const short min, const short max, const int dz, const float fsnow_lim, const char * histo_file=NULL);

void print_histogram (const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType & histogram, const char * histo_file);

#endif //HISTO_UTILS_H

