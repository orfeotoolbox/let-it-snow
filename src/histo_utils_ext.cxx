#include "histo_utils.h"
#include <boost/python.hpp>
 
BOOST_PYTHON_MODULE(histo_utils_ext)
{
    using namespace boost::python;
    def( "compute_zs", compute_zs );
    def( "compute_snow_fraction", compute_snow_fraction );
}
