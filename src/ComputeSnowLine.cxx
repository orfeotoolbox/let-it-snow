#include "otbWrapperApplication.h"
#include "otbWrapperApplicationFactory.h"
#include "otbWrapperChoiceParameter.h"

#include "histo_utils.h"
#include "otbStreamingMinMaxImageFilter.h"
#include "itkComposeImageFilter.h"

namespace otb
{
namespace Wrapper
{
class ComputeSnowLine : public Application
{
public:
  /** Standard class typedefs. */
  typedef ComputeSnowLine                Self;
  typedef Application                   Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  typedef Int16ImageType InputImageType;
  typedef otb::StreamingMinMaxImageFilter<InputImageType>     StreamingMinMaxImageFilterType;
  typedef itk::ComposeImageFilter<InputImageType> ComposeImageFilterType;
  
  /** Standard macro */
  itkNewMacro(Self)

  itkTypeMacro(ComputeSnowLine, otb::Wrapper::Application)

  private:
  void DoInit() override
  {
    SetName("ComputeSnowLine");
    SetDescription("Compute Snow line application");

    // Documentation
    //~ SetDocName("Application to compute the snow line");
    SetDocLongDescription("This application does compute the ZS value and output the histogram of snow pixels per altitude slices.");
    SetDocLimitations("None");
    SetDocAuthors("Manuel Grizonnet");
    SetDocSeeAlso("TODO");
    AddDocTag(Tags::Multi);

    AddParameter(ParameterType_InputImage, "dem", "Input DEM image");
    SetParameterDescription( "dem", "Input DEM image");
    
    AddParameter(ParameterType_InputImage, "ins", "Input snow image");
    SetParameterDescription( "ins", "Input snow image");

    AddParameter(ParameterType_InputImage, "inc", "Input cloud image");
    SetParameterDescription( "inc", "Input cloud image");

    AddParameter(ParameterType_Int, "dz", "Histogram altitude bin size");
    SetParameterDescription("dz", "Histogram altitude bin size");

    AddParameter(ParameterType_Float, "fsnowlim", "fsnowlim");
    SetParameterDescription("fsnowlim", "fsnowlim");

    AddParameter(ParameterType_Float, "fclearlim", "fclearlim");
    SetParameterDescription("fclearlim", "fclearlim");

    AddParameter(ParameterType_Int, "reverse", "reverse");
    SetParameterDescription("reverse", "reverse");

    AddParameter(ParameterType_Int, "offset", "offset");
    SetParameterDescription("offset", "offset");

    AddParameter(ParameterType_Int, "centeroffset", "centeroffset");
    SetParameterDescription("centeroffset", "centeroffset");
    
    AddRAMParameter();

    AddParameter(ParameterType_Int, "zs",  "ZS value");
    SetParameterDescription("zs", "zs value");
    SetParameterRole("zs", Role_Output);
    
    AddParameter(ParameterType_OutputFilename, "outhist", "Histogram");
    SetParameterDescription("outhist", "Histogram");
    
    SetDocExampleParameterValue("dem", "dem.tif");
    SetDocExampleParameterValue("ins", "snow.tif");
    SetDocExampleParameterValue("inc", "cloud.tif");
  }

  void DoUpdateParameters() override
  {
    // Nothing to do here : all parameters are independent
  }

  void DoExecute() override
  {
    // Read DEM image

    InputImageType * inDEMImage = GetParameterImage<InputImageType>("dem");

    // Instantiating object (compute min/max from dem image)
    m_Filter = StreamingMinMaxImageFilterType::New();

    // TODO Why setting the number of stripped lines here?
    m_Filter->GetStreamer()->SetNumberOfLinesStrippedStreaming( 10 );
    m_Filter->SetInput(inDEMImage);
    m_Filter->Update();

    InputImageType::PixelType min;
    InputImageType::PixelType max;

    min=m_Filter->GetMinimum();
    max=m_Filter->GetMaximum();

    otbAppLogINFO(<<"Min value in the DEM: " << min);
    otbAppLogINFO(<<"Max value in the DEM: " << max);
    // Read the snow and the cloud masks 
    
    InputImageType * inSnowImage = GetParameterImage<InputImageType>("ins");
    InputImageType * inCloudImage = GetParameterImage<InputImageType>("inc");
    
    //Concatenate dem, snow and cloud mask in one VectorImage
    m_ComposeFilter = ComposeImageFilterType::New();
    m_ComposeFilter->SetInput(0, inDEMImage);
    m_ComposeFilter->SetInput(1, inSnowImage);
    m_ComposeFilter->SetInput(2, inCloudImage);

    //Compute and return snowline
    const int zs = compute_snowline_internal(m_ComposeFilter->GetOutput(),
                                    min,
                                    max,
                                    GetParameterInt("dz"),
                                    GetParameterFloat("fsnowlim"),
                                    GetParameterFloat("fclearlim"),
                                    GetParameterInt("reverse")==1,
                                    GetParameterInt("offset"),
                                    GetParameterInt("centeroffset"),
                                    GetParameterAsString("outhist").c_str()
    );

    otbAppLogINFO(<<"ZS value computed: "<<zs);
    SetParameterInt("zs", zs, false);
  }

  StreamingMinMaxImageFilterType::Pointer m_Filter;
  ComposeImageFilterType::Pointer m_ComposeFilter;
};

}
}

OTB_APPLICATION_EXPORT(otb::Wrapper::ComputeSnowLine)

