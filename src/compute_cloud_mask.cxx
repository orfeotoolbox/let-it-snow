#include "itkUnaryCloudMaskImageFilter.h"
#include "otbImage.h"
#include "otbImageFileReader.h"
#include "otbImageFileWriter.h"
#include "otbStandardFilterWatcher.h"

int main(int argc, char * argv[])
{
  if (argc != 4)
    {
      std::cout << "<input_cloud_filename> <input_mask_value> <output_filename>" << std::endl;
    }

  const std::string cloud_fname = argv[1];
  const int cloud_mask_value = atoi(argv[2]);
  const std::string output_fname = argv[3];
  
  typedef otb::Image<unsigned char, 2>  InputImageType;
  typedef otb::Image<unsigned char, 2>  OutputImageType;

  typedef itk::UnaryCloudMaskImageFilter<InputImageType,OutputImageType> CloudMaskFilterType;
  typedef otb::ImageFileReader<InputImageType> ReaderType;
  typedef otb::ImageFileWriter<OutputImageType> WriterType;
  
  ReaderType::Pointer reader0 = ReaderType::New();
  reader0->SetFileName(cloud_fname);

  CloudMaskFilterType::Pointer filter = CloudMaskFilterType::New();
  filter->SetCloudMask(cloud_mask_value);

  filter->SetInput(0, reader0->GetOutput());

  WriterType::Pointer writer = WriterType::New();
  writer->SetFileName(output_fname);
  writer->SetInput(filter->GetOutput());

  otb::StandardFilterWatcher watcher(writer, "CloudMask");

  writer->Update();

  return EXIT_SUCCESS;
}
