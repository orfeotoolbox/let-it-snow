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

#include "histo_utils.h"
#include <boost/python.hpp>
 
BOOST_PYTHON_FUNCTION_OVERLOADS(compute_snowline_overloads, compute_snowline, 8, 9)

BOOST_PYTHON_MODULE(histo_utils_ext)
{
    using namespace boost::python;
    def( "compute_snowline", compute_snowline, compute_snowline_overloads(args("infname", "inmasksnowfname", "inmaskcloudfname", "dz", "fsnow_lim", "reverse", "offset", "center_offset", "histo_file"), "This is compute_snowline functions"));    
    def( "compute_nb_pixels_between_bounds", compute_nb_pixels_between_bounds );
}
