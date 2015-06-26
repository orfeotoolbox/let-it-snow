#include "compute_zs.h"

#include "otbStreamingHistogramMaskedVectorImageFilter.h"
#include "otbVectorImage.h"
#include "otbImage.h"
#include "otbImageFileReader.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "otbObjectList.h"
#include "itkHistogram.h"
#include "otbStreamingMinMaxVectorImageFilter.h"
 
int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname)
{
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


  VectorReaderType::Pointer reader = VectorReaderType::New();
  reader->SetFileName(infname);

  reader->UpdateOutputInformation();
  const unsigned int nbComp = reader->GetOutput()->GetNumberOfComponentsPerPixel();

  MaskReaderType::Pointer reader_snow = MaskReaderType::New();
  reader_snow->SetFileName(inmasksnowfname);

  MaskReaderType::Pointer reader_cloud = MaskReaderType::New();
  reader_cloud->SetFileName(inmaskcloudfname);

  // Instantiating object
  StreamingMinMaxImageFilterType::Pointer filter = StreamingMinMaxImageFilterType::New();

  filter->GetStreamer()->SetNumberOfLinesStrippedStreaming( 10 );
  filter->SetInput(reader->GetOutput());
  filter->Update();

  VectorImageType::PixelType min(nbComp);
  VectorImageType::PixelType max(nbComp);

  min=filter->GetMinimum();
  max=filter->GetMaximum();

  SHVIFType::Pointer SHVIFFilter1 = SHVIFType::New();
  SHVIFType::Pointer SHVIFFilter2 = SHVIFType::New();

  SHVIFFilter1->GetFilter()->SetInput(reader->GetOutput());
  SHVIFFilter2->GetFilter()->SetInput(reader->GetOutput());
  
  SHVIFType::FilterType::CountVectorType bins( nbComp );

  std::cout << "min " << filter->GetMinimum() << std::endl;
  std::cout << "max " << filter->GetMaximum() << std::endl;

  bins[0]=(max[0]-min[0]) / 100;
  
  SHVIFFilter1->GetFilter()->SetNumberOfBins( bins );
  SHVIFFilter1->GetFilter()->SetHistogramMin( min );
  SHVIFFilter1->GetFilter()->SetHistogramMax( max );
 
  SHVIFFilter2->GetFilter()->SetNumberOfBins( bins );
  SHVIFFilter2->GetFilter()->SetHistogramMin( min );
  SHVIFFilter2->GetFilter()->SetHistogramMax( max );

  //set mask
  SHVIFFilter1->SetMaskImage(reader_cloud->GetOutput());
  SHVIFFilter1->SetMaskValue(0);
  SHVIFFilter1->Update();

  SHVIFFilter2->SetMaskImage(reader_snow->GetOutput());
  SHVIFFilter2->SetMaskValue(1);
  SHVIFFilter2->Update();

  HistogramList::Pointer histograms1 = SHVIFFilter1->GetHistogramList();
  HistogramList::Pointer histograms2 = SHVIFFilter2->GetHistogramList();

  unsigned int channel = 0;  // first channel
  Histogram::Pointer histogram1( histograms1->GetNthElement( channel ) );
  Histogram::Pointer histogram2( histograms2->GetNthElement( channel ) );

  unsigned int histogramSize1 = histogram1->Size();

  std::cout << "Histogram size " << histogramSize1 << std::endl;

  for( unsigned int bin=0; bin < histogramSize1; bin++ )
    {
    std::cout << "Histogram 1 frequency " << histogram1->GetFrequency( bin, 0 ) << std::endl;
    std::cout << "Histogram 2 frequency " << histogram2->GetFrequency( bin, 0 ) << std::endl;
    std::cout << std::endl;

    if ((float) histogram2->GetFrequency( bin, 0 ) / (float) histogram1->GetFrequency( bin, 0 ) > 0.1)
      {
      std::cout << "Measurement vector at bin " << bin << " is "
            << histogram1->GetMeasurementVector(bin-2) << std::endl;
      return histogram1->GetMeasurementVector(bin-2)[0];
      }
    }

  return EXIT_SUCCESS;
}
