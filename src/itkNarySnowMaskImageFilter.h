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
#include "itkNaryFunctorImageFilter.h"
#include "itkNumericTraits.h"
#include <bitset>

namespace itk
{
namespace Functor
{
/**
 * \class SnowMask
 * \brief
 */
template< typename TInput, typename TOutput >
class SnowMask
{
public:
  typedef typename NumericTraits< TInput >::AccumulateType AccumulatorType;
  SnowMask() {}
  ~SnowMask() {}
  inline TOutput operator()(const std::vector< TInput > & B) const
  {
  std::bitset<8> bits(0x0);

  for ( unsigned int i = 0; i < B.size(); i++ )
    { 
    if ( B[i]>0 )
    { 
    bits.set(i,1);
    }
  }

  return static_cast< TOutput >( bits.to_ulong() );

  }

  bool operator==(const SnowMask &) const
  {
    return true;
  }

  bool operator!=(const SnowMask &) const
  {
    return false;
  }
};
}
/** \class NarySnowMaskImageFilter
 * \brief SnowMask  functor
 *
 */
template< typename TInputImage, typename TOutputImage >
class NarySnowMaskImageFilter:
  public
  NaryFunctorImageFilter< TInputImage, TOutputImage,
                          Functor::SnowMask< typename TInputImage::PixelType,  typename TInputImage::PixelType > >
{
public:
  /** Standard class typedefs. */
  typedef NarySnowMaskImageFilter Self;
  typedef NaryFunctorImageFilter<
    TInputImage, TOutputImage,
    Functor::SnowMask< typename TInputImage::PixelType,
                   typename TInputImage::PixelType > > Superclass;

  typedef SmartPointer< Self >       Pointer;
  typedef SmartPointer< const Self > ConstPointer;

  /** Method for creation through the object factory. */
  itkNewMacro(Self);

  /** Runtime information support. */
  itkTypeMacro(NarySnowMaskImageFilter,
               NaryFunctorImageFilter);

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
  NarySnowMaskImageFilter() {}
  virtual ~NarySnowMaskImageFilter() {}

private:
  NarySnowMaskImageFilter(const Self &);
  void operator=(const Self &);
};
} // end namespace itk

