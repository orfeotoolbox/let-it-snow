#include "otbWrapperApplication.h"
#include "otbWrapperApplicationFactory.h"
#include "otbWrapperChoiceParameter.h"
#include "otbImage.h"

#include "itkBinaryContourImageFilter.h"

namespace otb
{
namespace Wrapper
{
class ComputeContours : public Application
{
public:
    /** Standard class typedefs. */
    typedef ComputeContours               Self;
    typedef Application                   Superclass;
    typedef itk::SmartPointer<Self>       Pointer;
    typedef itk::SmartPointer<const Self> ConstPointer;

    typedef otb::Image<unsigned char, 2>  InputImageType;
    typedef otb::Image<unsigned char, 2>  OutputImageType;

    // Create a Binary Contour Image Filter
    typedef itk::BinaryContourImageFilter<InputImageType,InputImageType> ContourFilterType;

    /** Standard macro */
    itkNewMacro(Self)

    itkTypeMacro(ComputeContours, otb::Wrapper::Application)

    private:
        void DoInit() override
    {
        SetName("ComputeContours");
        SetDescription("Compute Contours application");

        // Documentation
        SetDocName("Application for Computing Contours");
        SetDocLongDescription("This application does compute the contours of the final mask");
        SetDocLimitations("None");
        SetDocAuthors("Germain SALGUES");
        SetDocSeeAlso("TODO");
        AddDocTag(Tags::Multi);

        AddParameter(ParameterType_InputImage, "inputmask", "mask image");
        SetParameterDescription( "inputmask", "Input mask to extract contours");
        MandatoryOn("inputmask");

        AddParameter(ParameterType_Float, "foregroundvalue", "foregroundvalue");
        SetParameterDescription( "foregroundvalue", "value corresponding to the region to extract");
        MandatoryOn("foregroundvalue");

        AddParameter(ParameterType_Float, "backgroundvalue", "backgroundvalue");
        SetParameterDescription( "backgroundvalue", "value corresponding to the mask background");

        AddParameter(ParameterType_Empty, "fullyconnected", "cloud refine image");
        SetParameterDescription( "fullyconnected", "Input cloud refine image");

        AddRAMParameter();

        AddParameter(ParameterType_OutputImage, "out",  "Output image");
        SetParameterDescription("out", "Output contour image");

        SetDocExampleParameterValue("inputmask", "input_mask.tif");
        SetDocExampleParameterValue("foregroundvalue", "255");
        SetDocExampleParameterValue("backgroundvalue", "0");
        SetDocExampleParameterValue("fullyconnected", "true");
        SetDocExampleParameterValue("out", "output_mask.tif");
    }

    virtual ~ComputeContours()
    {
    }

    void DoUpdateParameters() override
    {
        // Nothing to do here : all parameters are independent
    }

    void DoExecute() override
    {
        // Open list of inputs
        InputImageType::Pointer input_mask = GetParameterImage<InputImageType>("inputmask");

        m_ContourFilter = ContourFilterType::New();
        m_ContourFilter->SetInput(0, input_mask);
        m_ContourFilter->SetForegroundValue(GetParameterFloat("foregroundvalue"));
        m_ContourFilter->SetBackgroundValue(0);
        if(IsParameterEnabled("backgroundvalue")){
            m_ContourFilter->SetBackgroundValue(GetParameterFloat("backgroundvalue"));
        }
        m_ContourFilter->SetFullyConnected(IsParameterEnabled("fullyconnected"));

        // Set the output image
        SetParameterOutputImage("out", m_ContourFilter->GetOutput());
    }

    ContourFilterType::Pointer m_ContourFilter;
};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeContours)

