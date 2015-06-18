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

#include "otbStreamingHistogramMaskedVectorImageFilter.h"
#include "otbVectorImage.h"
#include "otbImage.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "otbObjectList.h"
#include "itkHistogram.h"

typedef otb::VectorImage<unsigned char>               VectorImageType;
typedef otb::Image<unsigned char>               MaskImageType;
typedef otb::StreamingHistogramMaskedVectorImageFilter<VectorImageType, MaskImageType>                SHVIFType;
typedef itk::NumericTraits< VectorImageType::InternalPixelType >::RealType RealType;
typedef RealType MeasurementType;
typedef itk::Statistics::Histogram< MeasurementType > Histogram;
typedef otb::ObjectList< Histogram > HistogramList;


int main(int itkNotUsed(argc), char * itkNotUsed(argv) [])
{
// Allocate input mask image
  const unsigned int nbComp = 2;
  MaskImageType::SizeType sizem;
  sizem.Fill(4);
  MaskImageType::IndexType idxm;
  idxm.Fill(0);
  MaskImageType::RegionType regionm;
  regionm.SetSize(sizem);
  regionm.SetIndex(idxm);

  MaskImageType::Pointer mask = MaskImageType::New();

  mask->SetRegions(regionm);
  mask->Allocate();

  typedef itk::ImageRegionIteratorWithIndex<MaskImageType> MaskIteratorType;
  MaskIteratorType maskit(mask, regionm);

  maskit.GoToBegin();
  MaskImageType::IndexType indexm;	
  while( !maskit.IsAtEnd() )
    {
    indexm = maskit.GetIndex();
    maskit.Set(indexm[0]);
    ++maskit;
    }
// Allocate input image

  VectorImageType::SizeType size;
  size.Fill(4);
  VectorImageType::IndexType idx;
  idx.Fill(0);
  VectorImageType::RegionType region;
  region.SetSize(size);
  region.SetIndex(idx);

  VectorImageType::Pointer image = VectorImageType::New();

  image->SetRegions(region);
  image->SetNumberOfComponentsPerPixel(nbComp);
  image->Allocate();

  typedef itk::ImageRegionIteratorWithIndex<VectorImageType> IteratorType;
  IteratorType it(image, region);

  it.GoToBegin();

  VectorImageType::PixelType pixel(nbComp);
  VectorImageType::IndexType index;

  while( !it.IsAtEnd() )
    {
    index = it.GetIndex();
    pixel[0]=index[0];
    pixel[1]=index[1];

    it.Set(pixel);
    ++it;
    }
//Histogram computation
  SHVIFType::Pointer SHVIFFilter = SHVIFType::New();

  SHVIFFilter->GetFilter()->SetInput(image);
  SHVIFType::FilterType::CountVectorType bins( nbComp );
  bins[0]=2;
  bins[1]=2;
  SHVIFFilter->GetFilter()->SetNumberOfBins( bins );

  VectorImageType::PixelType pixelMin(nbComp);
  pixelMin[0]=0;
  pixelMin[1]=0;
  VectorImageType::PixelType pixelMax(nbComp);
  pixelMax[0]=3;
  pixelMax[1]=3;

  SHVIFFilter->GetFilter()->SetHistogramMin( pixelMin );
  SHVIFFilter->GetFilter()->SetHistogramMax( pixelMax );
 
  //set mask
  SHVIFFilter->SetMaskImage(mask);
  
  MaskImageType::PixelType mask_val = 2;
  SHVIFFilter->SetMaskValue(mask_val);

  SHVIFFilter->Update();

  HistogramList::Pointer histograms = SHVIFFilter->GetHistogramList();

  std::cout << "Histogram list size " << histograms->Size() << std::endl;
  unsigned int channel = 0;  // first channel
  Histogram::Pointer histogram( histograms->GetNthElement( channel ) );

  unsigned int histogramSize = histogram->Size();

  std::cout << "Histogram size " << histogramSize << std::endl;

  

  std::cout << "Histogram of the first component" << std::endl;

 // We expect to have 2 bins, each with a frequency of 8.
  const unsigned int expectedFrequency = 8;

  for( unsigned int bin=0; bin < histogramSize; bin++ )
    {
    std::cout << "Histogram frequency " << histogram->GetFrequency( bin, 0 ) << std::endl;
    /*if( histogram->GetFrequency( bin, channel ) != expectedFrequency )
      {
      std::cerr << "Error in bin= " << bin << " channel = " << channel << std::endl;
      std::cerr << "Frequency was= " <<  histogram->GetFrequency( bin, 0 ) << " Instead of the expected " << expectedFrequency << std::endl;
      return EXIT_FAILURE;
      }*/
    }

  return EXIT_SUCCESS;
}
