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
#include "otbImageFileReader.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "otbObjectList.h"
#include "itkHistogram.h"
#include "otbStreamingMinMaxVectorImageFilter.h"

typedef otb::VectorImage<double>               VectorImageType;
typedef otb::Image<double, 2>               MaskImageType;
typedef otb::ImageFileReader<VectorImageType>               VectorReaderType;
typedef otb::ImageFileReader<MaskImageType>               MaskReaderType;
typedef otb::StreamingHistogramMaskedVectorImageFilter<VectorImageType, MaskImageType>                SHVIFType;
typedef itk::NumericTraits< VectorImageType::InternalPixelType >::RealType RealType;
typedef RealType MeasurementType;
typedef itk::Statistics::Histogram< MeasurementType > Histogram;
typedef otb::ObjectList< Histogram > HistogramList;
typedef otb::StreamingMinMaxVectorImageFilter<VectorImageType>     StreamingMinMaxImageFilterType;

int main(int argc, char * argv [])
{
  const char * infname = argv[1];
  const char * inmaskfname = argv[2];
  const int maskVal = atoi(argv[3]);

  VectorReaderType::Pointer reader = VectorReaderType::New();
  reader->SetFileName(infname);

  reader->UpdateOutputInformation();
  const unsigned int nbComp = reader->GetOutput()->GetNumberOfComponentsPerPixel();

  MaskReaderType::Pointer readerm = MaskReaderType::New();
  readerm->SetFileName(inmaskfname);

  // Instantiating object
  StreamingMinMaxImageFilterType::Pointer filter = StreamingMinMaxImageFilterType::New();

  filter->GetStreamer()->SetNumberOfLinesStrippedStreaming( 10 );
  filter->SetInput(reader->GetOutput());
  filter->Update();

  VectorImageType::PixelType min(nbComp);
  VectorImageType::PixelType max(nbComp);

  min=filter->GetMinimum();
  max=filter->GetMaximum();

  SHVIFType::Pointer SHVIFFilter = SHVIFType::New();

  SHVIFFilter->GetFilter()->SetInput(reader->GetOutput());
  SHVIFType::FilterType::CountVectorType bins( nbComp );

  std::cout << "min " << filter->GetMinimum() << std::endl;
  std::cout << "max " << filter->GetMaximum() << std::endl;

  bins[0]=(max[0]-min[0]) / 100;
  SHVIFFilter->GetFilter()->SetNumberOfBins( bins );

  SHVIFFilter->GetFilter()->SetHistogramMin( min );
  SHVIFFilter->GetFilter()->SetHistogramMax( max );
 
  //set mask
  SHVIFFilter->SetMaskImage(readerm->GetOutput());
  
  SHVIFFilter->SetMaskValue(maskVal);

  SHVIFFilter->Update();

  HistogramList::Pointer histograms = SHVIFFilter->GetHistogramList();

  unsigned int channel = 0;  // first channel
  Histogram::Pointer histogram( histograms->GetNthElement( channel ) );

  unsigned int histogramSize = histogram->Size();

  std::cout << "Histogram size " << histogramSize << std::endl;

  for( unsigned int bin=0; bin < histogramSize; bin++ )
    {
    std::cout << "Histogram frequency " << histogram->GetFrequency( bin, 0 ) << std::endl;
    }

  return EXIT_SUCCESS;
}
