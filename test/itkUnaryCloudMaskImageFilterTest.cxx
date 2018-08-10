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

#include "itkUnaryCloudMaskImageFilter.h"

int main(int argc, char * argv [])
{
  typedef unsigned short InputType;
  typedef unsigned char  OutputType;
  typedef itk::Functor::CloudMask<InputType, OutputType> FunctorType;
  
  FunctorType functor;

  const int inputCloudMaskValue = atoi(argv[1]);
  const int inputValue = atoi(argv[2]);
  functor.SetCloudMask(inputCloudMaskValue);

  OutputType result = static_cast<int>(functor(inputValue));
  
  if ( result != atoi(argv[3]))   
    {
      return EXIT_FAILURE;
    }
  else
    {
      return EXIT_SUCCESS;
    }
}
