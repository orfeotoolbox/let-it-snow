#include "compute_zs.h"
#include <boost/python.hpp>
 
BOOST_PYTHON_MODULE(compute_zs_ext)
{
    using namespace boost::python;
    def( "compute_zs", compute_zs );
}
