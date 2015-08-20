/*=========================================================================

  Program:   ORFEO Toolbox
  Language:  C++
  Date:      $Date$
  Version:   $Revision$


  Copyright (c) Centre National d'Etudes Spatiales. All rights reserved.
  See OTBCopyright.txt for details.


     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

=========================================================================*/

#include "histo_utils.h"
#include <iostream>
int main(int argc, char * argv [])
{
const int result = compute_zs_ng(argv[1],argv[2],argv[3],atoi(argv[4]),atof(argv[5]));
 const int expected = atoi(argv[6]); 
std::cout << "result: " << result << std::endl;
if (result == expected)
  {
  return EXIT_SUCCESS;
  }
else
  {
  std::cerr << "Expected value is " << expected << " but get " << result << std::endl; 
  return EXIT_FAILURE;
  }
}
