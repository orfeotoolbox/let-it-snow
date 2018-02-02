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
#include "itkImageRandomNonRepeatingIteratorWithIndex.h"
#include <iostream>

typedef itk::VectorImage< short, 2> ImageType;
const unsigned int MeasurementVectorSize = 3; // 3D vectors
void CreateImage(ImageType::Pointer image);

int main(int argc, char * argv [])
{
  const short minValue = atoi(argv[1]);
  const short maxValue = atoi(argv[2]);
  const int dz = atoi(argv[3]);
  const float fsnow_lim = atoi(argv[4]);
  const float fclear_lim = atoi(argv[5]);
  const bool reverse = atoi(argv[6]);
  const int offset = atoi(argv[7]);
  const int center_offset = atoi(argv[8]);
  const char * histo_path = argv[9];
  std::cout << "histo_path " << histo_path << std::endl;
  ImageType::Pointer image = ImageType::New();
  CreateImage(image);

  const int result = compute_snowline_internal(image,minValue,maxValue,dz,fsnow_lim,fclear_lim,reverse,offset,center_offset,histo_path);
  const int expected = atoi(argv[9]); 
  std::cout << "Computed zs: " << result << std::endl;

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

void CreateImage(ImageType::Pointer image)
{
  // Create a black image with a red square and a green square.
  // This should produce a histogram with very strong spikes.
  itk::Size<2> size;
  size.Fill(10);
  itk::Index<2> start;
  start.Fill(0);
  itk::ImageRegion<2> region(start, size);
  image->SetRegions(region);
  image->SetNumberOfComponentsPerPixel(MeasurementVectorSize);
  image->Allocate();
  
  ImageType::PixelType zeroPixel;
  zeroPixel.SetSize(MeasurementVectorSize);
  zeroPixel.Fill(0);
  
  image->FillBuffer(zeroPixel);
  
  ImageType::PixelType pixel;
  pixel.SetSize(MeasurementVectorSize);
  //pixel.Fill(110);
  pixel[0]=70;
  pixel[1]=1;
  pixel[2]=1;  

  itk::ImageRandomNonRepeatingIteratorWithIndex<ImageType> imageIterator(image, image->GetLargestPossibleRegion());
  imageIterator.ReinitializeSeed(0);  	
  imageIterator.SetNumberOfSamples(10);
 
  unsigned int counter=0;

  while(!imageIterator.IsAtEnd())
    {
    if (counter > 4)
      {
      //Change the pixel value at half of the iterations
      pixel[0]=81;
      pixel[1]=1;
      pixel[2]=0;
      }
    std::cout << "Setting pixel " << imageIterator.GetIndex() << " to " << pixel << std::endl;
    imageIterator.Set(pixel);
    ++imageIterator;
    ++counter;
    }
}

