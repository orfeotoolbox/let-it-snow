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

/**
 * \fn int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim)
 * \brief Function to compute zs elevation from dem image, snow mask from pass 1
 * and input cloud mask.
 *
 * \param input masks, elevation fraction (dz) and fsnow_lim
 * \return zs elevation. -1 if no zs was found
 * \deprecated Use compute_zs_ng and compute_zs_ng_internal to compute zs elevation
 */
int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim);

/**
 * \f int compute_nb_pixels_between_bounds(const std::string & infname, const int lowerbound, const int upperbound)
 * \brief Compute number of pixels between bounds
 */
int compute_nb_pixels_between_bounds(const std::string & infname, const int lowerbound, const int upperbound);

/**
 * \fn short compute_zs_ng(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim, const char * histo_file=NULL)
 * \brief Function to compute zs elevation from dem image, snow mask from pass 1
 * and input cloud mask.
 *
 * \param input masks, elevation fraction (dz) and fsnow_lim
 * \return zs elevation. -1 if no zs was found
 */
short compute_zs_ng(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim, const char * histo_file=NULL);

/**
 * \fn short compute_zs_ng_internal(const itk::VectorImage<short, 2>::Pointer compose_image, const short min, const short max, const int dz, const float fsnow_lim, const char * histo_file=NULL)
 * \brief Function to compute zs elevation from composite image (dem+snow+cloud)
 *
 * \param input composite image (concatenation of dem, snow and could mask), elevation fraction (dz) and fsnow_lim
 * \return zs elevation. -1 if no zs was found
 */
short compute_zs_ng_internal(const itk::VectorImage<short, 2>::Pointer compose_image, const short min, const short max, const int dz, const float fsnow_lim, const char * histo_file=NULL);

short compute_zs_max(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim, const char * histo_file=NULL);
short compute_zs_max_internal(const itk::VectorImage<short, 2>::Pointer compose_image, const short min, const short max, const int dz, const float fsnow_lim, const char * histo_file=NULL);

/**
 * \fn void print_histogram (const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType & histogram, const char * histo_file)
 * \brief Print histogram values to file (useful to validate)
 */
void print_histogram (const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType & histogram, const char * histo_file);

#endif //HISTO_UTILS_H

