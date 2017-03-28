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

#include "otbStreamingHistogramVectorImageFilter.h"
#include "otbStreamingHistogramMaskedVectorImageFilter.h"
#include "otbImage.h"
#include "otbVectorImage.h"
#include "otbImageFileReader.h"
#include "itkImageRegionIteratorWithIndex.h"
#include "otbObjectList.h"
#include "itkHistogram.h"
#include "otbStreamingMinMaxVectorImageFilter.h"
#include "otbStreamingMinMaxImageFilter.h"

#include "itkHistogram.h"
#include "itkComposeImageFilter.h"

#include <iostream>
#include <fstream>

#define CXX11_ENABLED (__cplusplus > 199711L )

//Deprecated
// int compute_zs(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim)
// {
//   typedef otb::VectorImage<double>               VectorImageType;
//   typedef otb::Image<double, 2>               MaskImageType;
//   typedef otb::ImageFileReader<VectorImageType>               VectorReaderType;
//   typedef otb::ImageFileReader<MaskImageType>               MaskReaderType;
//   typedef otb::StreamingHistogramMaskedVectorImageFilter<VectorImageType, MaskImageType>                SHVIFType;
//   typedef itk::NumericTraits< VectorImageType::InternalPixelType >::RealType RealType;
//   typedef RealType MeasurementType;
//   typedef itk::Statistics::Histogram< MeasurementType > Histogram;
//   typedef otb::ObjectList< Histogram > HistogramList;
//   typedef otb::StreamingMinMaxVectorImageFilter<VectorImageType>     StreamingMinMaxImageFilterType;


//   VectorReaderType::Pointer reader = VectorReaderType::New();
//   reader->SetFileName(infname);

//   reader->UpdateOutputInformation();
//   const unsigned int nbComp = reader->GetOutput()->GetNumberOfComponentsPerPixel();

//   MaskReaderType::Pointer reader_snow = MaskReaderType::New();
//   reader_snow->SetFileName(inmasksnowfname);

//   MaskReaderType::Pointer reader_cloud = MaskReaderType::New();
//   reader_cloud->SetFileName(inmaskcloudfname);

//   // Instantiating object
//   StreamingMinMaxImageFilterType::Pointer filter = StreamingMinMaxImageFilterType::New();

//   filter->GetStreamer()->SetNumberOfLinesStrippedStreaming( 10 );
//   filter->SetInput(reader->GetOutput());
//   filter->Update();

//   VectorImageType::PixelType min(nbComp);
//   VectorImageType::PixelType max(nbComp);

//   min=filter->GetMinimum();
//   max=filter->GetMaximum();

//   SHVIFType::Pointer SHVIFFilter1 = SHVIFType::New();
//   SHVIFType::Pointer SHVIFFilter2 = SHVIFType::New();

//   SHVIFFilter1->GetFilter()->SetInput(reader->GetOutput());
//   SHVIFFilter2->GetFilter()->SetInput(reader->GetOutput());
  
//   SHVIFType::FilterType::CountVectorType bins( nbComp );

//   // std::cout << "min " << filter->GetMinimum() << std::endl;
//   // std::cout << "max " << filter->GetMaximum() << std::endl;

//   bins[0]=(max[0]-min[0]) / dz;
  
//   SHVIFFilter1->GetFilter()->SetNumberOfBins( bins );
//   SHVIFFilter1->GetFilter()->SetHistogramMin( min );
//   SHVIFFilter1->GetFilter()->SetHistogramMax( max );
 
//   SHVIFFilter2->GetFilter()->SetNumberOfBins( bins );
//   SHVIFFilter2->GetFilter()->SetHistogramMin( min );
//   SHVIFFilter2->GetFilter()->SetHistogramMax( max );

//   //set mask
//   SHVIFFilter1->SetMaskImage(reader_cloud->GetOutput());
//   SHVIFFilter1->SetMaskValue(0);
//   SHVIFFilter1->Update();

//   SHVIFFilter2->SetMaskImage(reader_snow->GetOutput());
//   SHVIFFilter2->SetMaskValue(1);
//   SHVIFFilter2->Update();

//   HistogramList::Pointer histograms1 = SHVIFFilter1->GetHistogramList();
//   HistogramList::Pointer histograms2 = SHVIFFilter2->GetHistogramList();

//   unsigned int channel = 0;  // first channel
//   Histogram::Pointer histogram1( histograms1->GetNthElement( channel ) );
//   Histogram::Pointer histogram2( histograms2->GetNthElement( channel ) );

//   unsigned int histogramSize1 = histogram1->Size();
  
//   for( unsigned int bin=0; bin < histogramSize1; bin++ )
//     {/*
//     std::cout << "In bin=" << bin << ":" << std::endl;
//     std::cout << "Frequency in histogram1 = " <<  histogram1->GetFrequency( bin, channel ) << std::endl;
//     std::cout << "Measure in histogram1   = " <<  histogram1->GetMeasurementVector(bin)[0] << std::endl;
//     std::cout << std::endl;

//     std::cout << "Frequency in histogram2 = " <<  histogram2->GetFrequency( bin, channel ) << std::endl;
//     std::cout << "Measure in histogram2   = " <<  histogram2->GetMeasurementVector(bin)[0] << std::endl;*/
//     if ((float) histogram2->GetFrequency( bin, 0 ) / (float) histogram1->GetFrequency( bin, 0 ) > fsnow_lim)
//       {
//       if (bin >= 2)
//         {
//         //Return the min value of the bin (GetMeasurementVector returns the centroid)
//         return histogram1->GetMeasurementVector(bin-2)[0] - dz/2;
//         }
//       else
//         {
//         return histogram1->GetMeasurementVector(0)[0] - dz/2;
//         }
//       }
//     }

//   //Don't find a zs, return -1;
//   return -1;
// }

int compute_nb_pixels_between_bounds(const std::string & infname, const int lowerbound, const int upperbound)
{
  typedef otb::Image<short, 2> ImageType;
  typedef otb::ImageFileReader<ImageType> ReaderType;
  typedef itk::Statistics::ImageToHistogramFilter<ImageType> HistogramFilterType;

  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName(infname);

  HistogramFilterType::Pointer histogramFilter =
    HistogramFilterType::New();
  histogramFilter->SetInput(  reader->GetOutput()  );

  histogramFilter->SetAutoMinimumMaximum( false );
  histogramFilter->SetMarginalScale( 10000 );

  HistogramFilterType::HistogramMeasurementVectorType lowerBound(1);
  HistogramFilterType::HistogramMeasurementVectorType upperBound(1);

  lowerBound.Fill(lowerbound);
  //Bound set to 255 because of bad handling of tif 1 bits in OTB!
  //FIXME Change 255 to 0 when bug Mantis 1079 will be fixed
  upperBound.Fill(upperbound);
  
  histogramFilter->SetHistogramBinMinimum( lowerBound );
  histogramFilter->SetHistogramBinMaximum( upperBound );
  
  typedef HistogramFilterType::HistogramSizeType SizeType;
  SizeType size(1);

  size.Fill(2); 
  histogramFilter->SetHistogramSize( size );
  
  histogramFilter->Update();

  typedef HistogramFilterType::HistogramType  HistogramType;
  const HistogramType * histogram = histogramFilter->GetOutput();

  return histogram->GetFrequency(1);
}

void print_histogram (const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType & histogram, const char * histo_file)
{
  typedef itk::VectorImage<short, 2>  VectorImageType;
  typedef itk::Statistics::ImageToHistogramFilter<VectorImageType> HistogramFilterType;
  typedef HistogramFilterType::HistogramType  HistogramType;

  std::ofstream myfile;
  
#if CXX11_ENABLED
  myfile.open(std::string(histo_file));
#else
  myfile.open(histo_file);
#endif

  myfile << "Number of bins=" << histogram.Size()
         << "-Total frequency=" << histogram.GetTotalFrequency()
         << "-Dimension sizes=" << histogram.GetSize() << std::endl;

  myfile << "z_center,tot_z,fcloud_z,fsnow_z,fnosnow_z" << std::endl;

  for (unsigned int i=0;i<histogram.GetSize()[0]; ++i)
    {
    HistogramType::IndexType idx1(3);
    idx1[0] = i;
    idx1[1] = 0;
    idx1[2] = 0;

    HistogramType::IndexType idx2(3);
    idx2[0] = i;
    idx2[1] = 1;
    idx2[2] = 0;

    HistogramType::IndexType idx3(3);
    idx3[0] = i;
    idx3[1] = 0;
    idx3[2] = 1;

    HistogramType::IndexType idx4(3);
    idx4[0] = i;
    idx4[1] = 1;
    idx4[2] = 1;

    const HistogramType::AbsoluteFrequencyType z_center = histogram.GetMeasurementVector(idx1)[0];
    const int Nz = histogram.GetFrequency(idx1) + histogram.GetFrequency(idx2) + histogram.GetFrequency(idx3) + histogram.GetFrequency(idx4);
    const int fcloud_z = histogram.GetFrequency(idx3) + histogram.GetFrequency(idx4);
    const int fsnow_z = histogram.GetFrequency(idx2) + histogram.GetFrequency(idx4);
    const int fnosnow_z = histogram.GetFrequency(idx1);

    myfile << z_center << "," << Nz << "," << fcloud_z << "," << fsnow_z << "," << fnosnow_z << std::endl;
    }

  myfile.close();
}

// compute and return snowline

short compute_snowline(const std::string & infname, const std::string & inmasksnowfname, const std::string & inmaskcloudfname, const int dz, const float fsnow_lim, const bool reverse, const int offset, const int center_offset, const char * histo_file)
{
  /** Filters typedef */
  typedef otb::Image<short, 2>                           ImageType;
  typedef otb::ImageFileReader<ImageType>                ReaderType;
  typedef otb::StreamingMinMaxImageFilter<ImageType>     StreamingMinMaxImageFilterType;

  ReaderType::Pointer reader = ReaderType::New();
  reader->SetFileName(infname);

  // Instantiating object (compute min/max from dem image)
  StreamingMinMaxImageFilterType::Pointer filter = StreamingMinMaxImageFilterType::New();

  filter->GetStreamer()->SetNumberOfLinesStrippedStreaming( 10 );
  filter->SetInput(reader->GetOutput());
  filter->Update();

  ImageType::PixelType min;
  ImageType::PixelType max;

  min=filter->GetMinimum();
  max=filter->GetMaximum();

  typedef itk::ComposeImageFilter<ImageType> ImageToVectorImageFilterType;

  ReaderType::Pointer reader_snow = ReaderType::New();
  reader_snow->SetFileName(inmasksnowfname);

  ReaderType::Pointer reader_cloud = ReaderType::New();
  reader_cloud->SetFileName(inmaskcloudfname);

  //Concatenate dem, snow and cloud mask in one VectorImage
  ImageToVectorImageFilterType::Pointer imageToVectorImageFilter = ImageToVectorImageFilterType::New();
  imageToVectorImageFilter->SetInput(0, reader->GetOutput());
  imageToVectorImageFilter->SetInput(1, reader_snow->GetOutput());
  imageToVectorImageFilter->SetInput(2, reader_cloud->GetOutput());

  //Compute and return snowline
  return compute_snowline_internal(imageToVectorImageFilter->GetOutput(), min, max, dz, fsnow_lim, reverse, offset, center_offset, histo_file);
}

short compute_snowline_internal(const itk::VectorImage<short, 2>::Pointer compose_image, const short min, const short max, const int dz, const float fsnow_lim, const bool reverse, const int offset, const int center_offset,  const char* histo_file)
{
  typedef itk::VectorImage<short, 2>  VectorImageType;
  typedef itk::Statistics::ImageToHistogramFilter<VectorImageType> HistogramFilterType;

  HistogramFilterType::Pointer histogramFilter =
    HistogramFilterType::New();
  histogramFilter->SetInput(  compose_image  );

  histogramFilter->SetAutoMinimumMaximum( false );
  histogramFilter->SetMarginalScale( 10000 );

  HistogramFilterType::HistogramMeasurementVectorType lowerBound( 3 );
  HistogramFilterType::HistogramMeasurementVectorType upperBound( 3 );

  lowerBound[0] = min;
  lowerBound[1] = 0;
  lowerBound[2] = 0;
  upperBound[0] = max;
  //Bound set to 255 because of bad handling of tif 1 bits in OTB!
  //FIXME Change 255 to 0 when bug Mantis 1079 will be fixed
  upperBound[1] = 255;
  upperBound[2] = 255;

  histogramFilter->SetHistogramBinMinimum( lowerBound );
  histogramFilter->SetHistogramBinMaximum( upperBound );
  
  typedef HistogramFilterType::HistogramSizeType SizeType;
  SizeType size( 3 );

  size[0] = (upperBound[0]-lowerBound[0]) / dz;        // number of bins for the altitude   channel
  size[1] =   2;        // number of bins for the snow channel
  size[2] =   2;        // number of bins for the cloud  channel

  histogramFilter->SetHistogramSize( size );
  
  histogramFilter->Update();
  typedef HistogramFilterType::HistogramType  HistogramType;
  const HistogramType * histogram = histogramFilter->GetOutput();


  //Print the histogram (log and debug info)
  if ( histo_file != NULL )
    {
      print_histogram(*histogram,histo_file);
    }
  short snowline = -1;
  if(reverse)
    {
      for (int i=histogram->GetSize()[0]-1; i>=0; i--)
	{
	  snowline = get_elev_snowline_from_bin(histogram, i, fsnow_lim, offset, center_offset);
	  if(snowline != -1)
	    return snowline;
	}
    }
  else
    {
      for (unsigned int i=0; i<histogram->GetSize()[0]; ++i)
	{
	  snowline = get_elev_snowline_from_bin(histogram, i, fsnow_lim, offset, center_offset);
	  if(snowline != -1)
	    return snowline;
	}
    }
  // snow line not found -1
  return snowline;
}

short get_elev_snowline_from_bin(const itk::Statistics::ImageToHistogramFilter<itk::VectorImage<short, 2> >::HistogramType* histogram, const unsigned int i, const float fsnow_lim, const int offset, const  int center_offset)
{
  typedef itk::VectorImage<short, 2>  VectorImageType;
  typedef itk::Statistics::ImageToHistogramFilter<VectorImageType> HistogramFilterType;
  typedef HistogramFilterType::HistogramType  HistogramType;

  HistogramType::IndexType idx1(3);
  idx1[0] = i;
  idx1[1] = 0;
  idx1[2] = 0;
  
  HistogramType::IndexType idx2(3);
  idx2[0] = i;
  idx2[1] = 1;
  idx2[2] = 0;
  
  //Compute the total number of pixels (snow+no snow) cloud free in the elevation cell
  const HistogramType::AbsoluteFrequencyType z=histogram->GetFrequency(idx1) + histogram->GetFrequency(idx2);
  //If there are pixels in this elevation cell and Check if there is enough snow pixel
  if ( (z != 0) && ( ( static_cast<double> (histogram->GetFrequency(idx2)) / static_cast<double> (z) ) > fsnow_lim ) )
    {	    
      HistogramType::IndexType idx_res(3);
      idx_res[0] = std::max(static_cast<int>(i+offset),0);
      idx_res[1] = 1;
      idx_res[2] = 0;
      
      return vcl_floor(histogram->GetMeasurementVector(idx_res)[0] + center_offset);
    }
  else
    {
      return -1;
    }  
} 

