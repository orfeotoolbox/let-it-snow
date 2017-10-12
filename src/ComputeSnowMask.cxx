#include "otbWrapperApplication.h"
#include "otbWrapperApplicationFactory.h"
#include "otbWrapperChoiceParameter.h"

#include "itkNarySnowMaskImageFilter.h"
#include "otbImage.h"

namespace otb
{
namespace Wrapper
{
class ComputeSnowMask : public Application
{
public:
  /** Standard class typedefs. */
  typedef ComputeSnowMask               Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  typedef otb::Image<unsigned char, 2>  InputImageType;
  typedef otb::Image<unsigned char, 2>  OutputImageType;

  // Create an SnowMask Filter
  typedef itk::NarySnowMaskImageFilter<InputImageType,OutputImageType>  SnowMaskFilterType;

  /** Standard macro */
  itkNewMacro(Self)

  itkTypeMacro(ComputeSnowMask, otb::Wrapper::Application)

  private:
  void DoInit() override
  {
    SetName("ComputeSnowMask");
    SetDescription("Compute Snow Mask application");

    // Documentation
    SetDocName("Application for Compute Snow Mask");
    SetDocLongDescription("This application does compute the snow mask");
    SetDocLimitations("None");
    SetDocAuthors("Germain SALGUES");
    SetDocSeeAlso("TODO");
    AddDocTag(Tags::Multi);

    AddParameter(ParameterType_InputImage, "pass1", "pass1 image");
    SetParameterDescription( "pass1", "Input pass1 image");
    MandatoryOn("pass1");

    AddParameter(ParameterType_InputImage, "pass2", "pass2 image");
    SetParameterDescription( "pass2", "Input pass2 image");
    MandatoryOn("pass2");

    AddParameter(ParameterType_InputImage, "cloudpass1", "cloud pass1 image");
    SetParameterDescription( "cloudpass1", "Input cloud pass1 image");
    MandatoryOn("cloudpass1");

    AddParameter(ParameterType_InputImage, "cloudrefine", "cloud refine image");
    SetParameterDescription( "cloudrefine", "Input cloud refine image");
    MandatoryOn("cloudrefine");

    AddRAMParameter();

    AddParameter(ParameterType_OutputImage, "out",  "Output image");
    SetParameterDescription("out", "Output cloud mask");

    SetDocExampleParameterValue("pass1", "pass1.tif");
    SetDocExampleParameterValue("pass2", "pass2.tif");
    SetDocExampleParameterValue("cloudpass1", "cloud_pass1.tif");
    SetDocExampleParameterValue("cloudrefine", "cloud_refine.tif");
    SetDocExampleParameterValue("out", "output_mask.tif");
  }

  virtual ~ComputeSnowMask()
  {
  }

  void DoUpdateParameters() override
  {
    // Nothing to do here : all parameters are independent
  }

  void DoExecute() override
  {
    // Open list of inputs
    InputImageType::Pointer img_pass1 = GetParameterImage<InputImageType>("pass1");
    InputImageType::Pointer img_pass2 = GetParameterImage<InputImageType>("pass2");
    InputImageType::Pointer img_cloud_pass1 = GetParameterImage<InputImageType>("cloudpass1");
    InputImageType::Pointer img_cloud_refine = GetParameterImage<InputImageType>("cloudrefine");

    m_SnowMaskFilter = SnowMaskFilterType::New();
    m_SnowMaskFilter->SetInput(0, img_pass1);
    m_SnowMaskFilter->SetInput(1, img_pass2);
    m_SnowMaskFilter->SetInput(2, img_cloud_pass1);
    m_SnowMaskFilter->SetInput(3, img_cloud_refine);

    // Set the output image
    SetParameterOutputImage("out", m_SnowMaskFilter->GetOutput());
  }

  SnowMaskFilterType::Pointer m_SnowMaskFilter;

};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeSnowMask)

