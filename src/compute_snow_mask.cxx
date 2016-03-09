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
#include "itkNarySnowMaskImageFilter.h"
#include "otbImage.h"
#include "otbImageFileReader.h"
#include "otbImageFileWriter.h"
#include "otbStandardFilterWatcher.h"

int main(int argc, char * argv[])
{
  if (argc != 6)
    {
    std::cout << argv[0] << " <input_pass1_filename> <input_pass2_filename> ";
    std::cout << "<input_cloud_pass1_filename> <input_cloud_refine_filename> <output_filename>  "<< std::endl;

    return EXIT_FAILURE;
    }

  const std::string pass1_fname = argv[1];
  const std::string pass2_fname = argv[2];
  const std::string cloud_pass1_fname = argv[3];
  const std::string cloud_refine_fname = argv[4];
  const std::string outname = argv[5];

  typedef otb::Image<unsigned char, 2>  InputImageType;
  typedef otb::Image<unsigned char, 2>  OutputImageType;
  // Create an SnowMask Filter
  typedef itk::NarySnowMaskImageFilter<
    InputImageType,
    OutputImageType  >  SnowMaskFilterType;
  typedef otb::ImageFileReader<InputImageType>               ReaderType;
  typedef otb::ImageFileWriter<OutputImageType>               WriterType;

  ReaderType::Pointer reader0 = ReaderType::New();
  reader0->SetFileName(pass1_fname);
  ReaderType::Pointer reader1 = ReaderType::New();
  reader1->SetFileName(pass2_fname);
  ReaderType::Pointer reader2 = ReaderType::New();
  reader2->SetFileName(cloud_pass1_fname);
  ReaderType::Pointer reader3 = ReaderType::New();
  reader3->SetFileName(cloud_refine_fname);
  
  SnowMaskFilterType::Pointer filter = SnowMaskFilterType::New();

  filter->SetInput(0, reader0->GetOutput());
  filter->SetInput(1, reader1->GetOutput());
  filter->SetInput(2, reader2->GetOutput());
  filter->SetInput(3, reader3->GetOutput());

  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(outname);
  writer->SetInput(filter->GetOutput());

  otb::StandardFilterWatcher watcher(writer, "SnowMask");

  writer->Update();

  return EXIT_SUCCESS;
}
