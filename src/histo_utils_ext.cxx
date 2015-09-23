#include "histo_utils.h"
#include <boost/python.hpp>
 
//Declare overloaded functions to allow to pass null value for the histogram
BOOST_PYTHON_FUNCTION_OVERLOADS(compute_zs_ng_overloads, compute_zs_ng, 5, 6)

BOOST_PYTHON_MODULE(histo_utils_ext)
{
    using namespace boost::python;
    def( "compute_zs", compute_zs );
    

    def( "compute_zs_ng", compute_zs_ng, compute_zs_ng_overloads(
            args("infname", "inmasksnowfname", "inmaskcloudfname", "dz", "fsnow_lim", "histo_file"), "This is compute_zs_ng functions"
        ));

    

    def( "compute_snow_fraction", compute_snow_fraction );
}
