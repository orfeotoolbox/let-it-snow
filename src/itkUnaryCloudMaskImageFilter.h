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
      CloudMask() {}
      ~CloudMask(){}

      void SetCloudMask(const unsigned int val)
      {
        m_cloud_mask_value = val;
      }

      inline TOutput operator()(const TInput& B) const
      {
        std::bitset<8> bits(B);
        std::bitset<8> mask_bits(m_cloud_mask_value);
        std::bitset<8> result;
        result = bits & mask_bits;
        if(result != 0)
          return static_cast<TOutput>(1);
        else
          return static_cast<TOutput>(0);

        /* if(result.to_ulong()>0) */
        /*   return static_cast<TOutput>(1); */
        /* else */
        /*   return static_cast<TOutput>(0); */
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
      int m_cloud_mask_value;
    };
  }
  // Description functor
  template<typename TInputImage, typename TOutputImage> class UnaryCloudMaskImageFilter:
    public
    UnaryFunctorImageFilter< TInputImage, TOutputImage,
                            Functor::CloudMask< typename TInputImage::PixelType, typename TInputImage::PixelType > >
  {
  public:
    typedef UnaryCloudMaskImageFilter Self;
    typedef UnaryFunctorImageFilter<
    TInputImage, TOutputImage,
    Functor::CloudMask< typename TInputImage::PixelType,
                   typename TInputImage::PixelType > > Superclass;

  typedef SmartPointer< Self >       Pointer;
  typedef SmartPointer< const Self > ConstPointer;

  void SetCloudMask(const unsigned int val)
  {
    this->GetFunctor().SetCloudMask(val);
  }
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
