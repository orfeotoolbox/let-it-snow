#include "itkUnaryFunctorImageFilter.h"
#include "itkNumericTraits.h"
#include <bitset>


namespace itk
{
  namespace Functor
  {
    // Description class
    
    template<typename TInput, typename TOutput> class CloudMask
    {
    public:
      typedef typename NumericTraits< TInput >::AccumulateType AccumulatorType;
      CloudMask(const int cloud_mask_value) : m_cloud_mask_value(cloud_mask_value) {}
      ~CloudMask(){}
      
      inline TOutput operator()(const TInput& B) const
      {
	std::bitset<8> bits(B);
	std::bitset<8> mask_bits(m_cloud_mask_value);
	std::bitset<8> result(bits & mask_bits);
	if(result>0)
	  return static_cast<TOutput>(1);
	else
	  return static_cast<TOutput>(0)
      }
      bool operator==(const CloudMask &) const
      {
	return true;
      }
      
      bool operator!=(const CloudMask &) const
      {
	return false;
      }
    private:
      int m_cloud_mask_value
    };
  }
  // Description functor
  template<typename TInputImage, typename TOutputImage> class UnaryCloudMaskImageFilter:
    public 
    UnaryFunctorImageFilter<TInputImage, TOutputImage, 
                            Functor::CloudMask<typename TInputimage::PixelType, typename TInputImage::PixelType>>
  {
  public:
    typedef UnaryCloudMakImageFilter Self;
    typedef UnaryFunctorImageFilter<
    TInputImage, TOutputImage,
    Functor::CloudMask< typename TInputImage::PixelType,
                   typename TInputImage::PixelType > > Superclass;

  typedef SmartPointer< Self >       Pointer;
  typedef SmartPointer< const Self > ConstPointer;

  /** Method for creation through the object factory. */
  itkNewMacro(Self);

  /** Runtime information support. */
  itkTypeMacro(UnaryCloudMaskImageFilter,
               UnaryFunctorImageFilter);

#ifdef ITK_USE_CONCEPT_CHECKING
  // Begin concept checking
  itkConceptMacro( InputConvertibleToOutputCheck,
                   ( Concept::Convertible< typename TInputImage::PixelType,
                                           typename TOutputImage::PixelType > ) );
  itkConceptMacro( InputHasZeroCheck,
                   ( Concept::HasZero< typename TInputImage::PixelType > ) );
  // End concept checking
#endif

  protected:
  UnaryCloudMaskImageFilter() {}
  virtual ~UnaryCloudMaskImageFilter() {}

  private:
  UnaryCloudMaskImageFilter(const Self &);
  void operator=(const Self &);

  };
}
