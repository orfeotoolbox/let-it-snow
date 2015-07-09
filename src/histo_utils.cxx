#include "histo_utils.h"

#include "otbStreamingHistogramVectorImageFilter.h"
#include "otbStreamingHistogramMaskedVectorImageFilter.h"
#include "otbVectorImage.h"
#include "otbImage.h"
#include "otbImageFileReader.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "otbObjectList.h"
#include "itkHistogram.h"
#include "otbStreamingMinMaxVectorImageFilter.h"
 
int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim)
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

  // std::cout << "min " << filter->GetMinimum() << std::endl;
  // std::cout << "max " << filter->GetMaximum() << std::endl;

  bins[0]=(max[0]-min[0]) / dz;
  
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
  
  for( unsigned int bin=0; bin < histogramSize1; bin++ )
    {
    std::cout << "In bin=" << bin << ":" << std::endl;
    std::cout << "Frequency in histogram1 = " <<  histogram1->GetFrequency( bin, channel ) << std::endl;
    std::cout << "Measure in histogram1   = " <<  histogram1->GetMeasurementVector(bin)[0] << std::endl;
    std::cout << std::endl;

    std::cout << "Frequency in histogram2 = " <<  histogram2->GetFrequency( bin, channel ) << std::endl;
    std::cout << "Measure in histogram2   = " <<  histogram2->GetMeasurementVector(bin)[0] << std::endl;
    if ((float) histogram2->GetFrequency( bin, 0 ) / (float) histogram1->GetFrequency( bin, 0 ) > fsnow_lim)
      {
      if (bin >= 2)
        {
	//Return the min valu of the bin (GetMeasurementVector returns the centroid)
        return histogram1->GetMeasurementVector(bin-2)[0] - dz/2;
        }
      else
        {
        return histogram1->GetMeasurementVector(0)[0] - dz/2;
        }
      }
    }

  //Don't find a zs, return -1;
  return -1;
}

int compute_snow_fraction(const std::string & infname)
{
  typedef otb::VectorImage<unsigned char>               VectorImageType;
  typedef otb::Image<unsigned char, 2>               MaskImageType;
  typedef otb::ImageFileReader<VectorImageType>               VectorReaderType;
  typedef otb::ImageFileReader<MaskImageType>               MaskReaderType;
  typedef otb::StreamingHistogramMaskedVectorImageFilter<VectorImageType, MaskImageType>                SHVIFType;

  const unsigned int nbComp = VectorImageType::ImageDimension;

  VectorReaderType::Pointer reader = VectorReaderType::New();
  reader->SetFileName(infname);
  reader->UpdateOutputInformation();

  MaskReaderType::Pointer readerMask = MaskReaderType::New();
  readerMask->SetFileName(infname);

  SHVIFType::Pointer SHVIFFilter = SHVIFType::New();
  SHVIFFilter->GetFilter()->SetInput(reader->GetOutput());

  VectorImageType::PixelType pixelMin(nbComp);
  pixelMin[0]=0;
  pixelMin[1]=0;
  VectorImageType::PixelType pixelMax(nbComp);
  pixelMax[0]=1;
  pixelMax[1]=1;

  SHVIFType::FilterType::CountVectorType bins( nbComp );
  bins[0]=1;
  bins[1]=1;
  SHVIFFilter->GetFilter()->SetNumberOfBins( bins );

  SHVIFFilter->GetFilter()->SetHistogramMin( pixelMin );
  SHVIFFilter->GetFilter()->SetHistogramMax( pixelMax );

  SHVIFFilter->SetMaskImage(readerMask->GetOutput());
  SHVIFFilter->SetMaskValue(1);

  SHVIFFilter->Update();
  
  return SHVIFFilter->GetHistogramList()->GetNthElement(0)->GetFrequency(0,0);
}
