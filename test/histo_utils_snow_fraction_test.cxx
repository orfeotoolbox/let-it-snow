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
#include "otbImageFileWriter.h"
#include "itkImageRandomNonRepeatingIteratorWithIndex.h"
#include <iostream>

typedef itk::VectorImage< short, 2> ImageType;
const unsigned int MeasurementVectorSize = 1; // 3D vectors

void CreateImage(ImageType::Pointer image, const int nbSamples, const int pixValue);

int main(int argc, char * argv [])
{
  const int expected = atoi(argv[2]);

  const int pixValue = 255;
  
  ImageType::Pointer image = ImageType::New();
  CreateImage(image, expected, pixValue);

  //Write image to temporary directory
  typedef otb::ImageFileWriter<ImageType> WriterType;
  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(argv[1]);
  writer->SetInput(image);
  writer->Update();
  
  //Then apply computation to the temporary image
  const int result = compute_nb_pixels_between_bounds(argv[1], 0, pixValue);
  
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

void CreateImage(ImageType::Pointer image, const int nbSamples, const int pixValue)
{
  const int imgSize = nbSamples*nbSamples;
  
  // Create a black image.
  itk::Size<2> size;
  size.Fill(imgSize);
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
  pixel[0]=pixValue;

  itk::ImageRandomNonRepeatingIteratorWithIndex<ImageType> imageIterator(image, image->GetLargestPossibleRegion());
  imageIterator.ReinitializeSeed(0);  	
  imageIterator.SetNumberOfSamples(nbSamples);
 
  while(!imageIterator.IsAtEnd())
    {
    imageIterator.Set(pixel);
    ++imageIterator;
    }
}
