/*=========================================================================

  Program:   ORFEO Toolbox
  Language:  C++
  Date:      $Date$
  Version:   $Revision$


  Copyright (c) Centre National d'Etudes Spatiales. All rights reserved.
  See OTBCopyright.txt for details.

  Some parts of this code are derived from ITK. See ITKCopyright.txt
  for details.


     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANT2ABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notices for more information.

=========================================================================*/
#ifndef __otbStreamingHistogramMaskedVectorImageFilter_h
#define __otbStreamingHistogramMaskedVectorImageFilter_h

#include "otbPersistentImageFilter.h"
#include "otbPersistentFilterStreamingDecorator.h"

#include "otbObjectList.h"
#include "itkStatisticsAlgorithm.h"
#include "itkNumericTraits.h"
#include "itkHistogram.h"
#include "itkSimpleDataObjectDecorator.h"
#include "itkMacro.h"

/** Set a decorated input. This defines the Set"name"() and a Set"name"Input() method */
#define otbSetDecoratedInputMacro(name, type)                                                                 \
  virtual void Set##name##Input(const itk::SimpleDataObjectDecorator< type > *_arg)                                \
    {                                                                                                         \
    itkDebugMacro("setting input " #name " to " << _arg);                                                     \
    if ( _arg != itkDynamicCastInDebugMode< itk::SimpleDataObjectDecorator< type > * >( this->itk::ProcessObject::GetInput(#name) ) ) \
      {                                                                                                       \
      this->itk::	ProcessObject::SetInput( #name, const_cast< itk::SimpleDataObjectDecorator< type > * >( _arg ) );      \
      this->Modified();                                                                                       \
      }                                                                                                       \
    }                                                                                                         \
  virtual void Set##name(const type &_arg)                           \
    {                                                                \
    typedef itk::SimpleDataObjectDecorator< type > DecoratorType;         \
    itkDebugMacro("setting input " #name " to " << _arg);            \
    const DecoratorType *oldInput =                                  \
      itkDynamicCastInDebugMode< const DecoratorType * >(            \
        this->ProcessObject::GetInput(#name) );                      \
    if ( oldInput && oldInput->Get() == _arg )                       \
      {                                                              \
      return;                                                        \
      }                                                              \
    typename DecoratorType::Pointer newInput = DecoratorType::New(); \
    newInput->Set(_arg);                                             \
    this->Set##name##Input(newInput);                                \
    }

/** Set a decorated input. This defines the Set"name"() and Set"name"Input() method */
#define otbGetDecoratedInputMacro(name, type)                                                                 \
  virtual const itk::SimpleDataObjectDecorator< type > * Get##name##Input() const                                                                 \
    {                                                                                                                                        \
    itkDebugMacro( "returning input " << #name " of " << this->ProcessObject::GetInput(#name) );                                             \
    return itkDynamicCastInDebugMode< const itk::SimpleDataObjectDecorator< type > * >( this->ProcessObject::GetInput(#name) );                   \
    }                                                                \
  virtual const type & Get##name() const                             \
    {                                                                \
    itkDebugMacro("Getting input " #name);                           \
    typedef itk::SimpleDataObjectDecorator< type > DecoratorType;         \
    const DecoratorType *input =                                     \
      itkDynamicCastInDebugMode< const DecoratorType * >(            \
        this->ProcessObject::GetInput(#name) );                      \
    if( input == ITK_NULLPTR )                                       \
      {                                                              \
      itkExceptionMacro(<<"input" #name " is not set");              \
      }                                                              \
    return input->Get();                                             \
    }

/** Set a decorated input. This defines the Set"name"() and Set"name"Input() method
 * and Get"name" and Get"name"Input methods */
#define otbSetGetDecoratedInputMacro(name, type)  \
  otbSetDecoratedInputMacro(name, type)           \
  otbGetDecoratedInputMacro(name, type)

namespace otb
{

/** class PersistentHistogramMaskedVectorImageFilter
 * brief Compute the histogram of a large image using streaming
 *
 *  This filter persists its temporary data. It means that if you Update it n times on n different
 * requested regions, the output histogram will be the histogram of the whole set of n regions.
 *
 * To reset the temporary data, one should call the Reset() function.
 *
 * To get the histogram once the regions have been processed via the pipeline, use the Synthetize() method.
 *
 * sa PersistentImageFilter
 * ingroup Streamed
 * ingroup Multithreaded
 * ingroup MathematicalStatisticsImageFilters
 *
 *
 * ingroup OTBStatistics
 */
template<class TInputImage, class TMaskImage>
class ITK_EXPORT PersistentHistogramMaskedVectorImageFilter :
  public PersistentImageFilter<TInputImage, TInputImage>
{
public:
  /** Standard Self typedef */
  typedef PersistentHistogramMaskedVectorImageFilter               Self;
  typedef PersistentImageFilter<TInputImage, TInputImage> Superclass;
  typedef itk::SmartPointer<Self>                         Pointer;
  typedef itk::SmartPointer<const Self>                   ConstPointer;

  /** Method for creation through the object factory. */
  itkNewMacro(Self);

  /** Runtime information support. */
  itkTypeMacro(PersistentHistogramMaskedVectorImageFilter, PersistentImageFilter);

  /** Image related typedefs. */
  typedef TInputImage                             ImageType;
  typedef typename TInputImage::Pointer           InputImagePointer;
  typedef typename TInputImage::RegionType        RegionType;
  typedef typename TInputImage::SizeType          SizeType;
  typedef typename TInputImage::IndexType         IndexType;
  typedef typename TInputImage::PixelType         PixelType;
  typedef typename TInputImage::InternalPixelType InternalPixelType;

  itkStaticConstMacro(InputImageDimension, unsigned int, TInputImage::ImageDimension);

  /** Image related typedefs. */
  itkStaticConstMacro(ImageDimension, unsigned int, TInputImage::ImageDimension);

  /** Type to use for computations. */
  typedef typename itk::NumericTraits<InternalPixelType>::RealType RealType;
  typedef itk::VariableLengthVector<RealType>                      RealPixelType;

  /** Smart Pointer type to a DataObject. */
  typedef typename itk::DataObject::Pointer       DataObjectPointer;
  typedef itk::ProcessObject::DataObjectPointerArraySizeType DataObjectPointerArraySizeType;

  /** Types for histogram */
  typedef itk::Statistics::DenseFrequencyContainer2        DFContainerType;

  typedef
    typename itk::NumericTraits<InternalPixelType>::RealType
    HistogramMeasurementRealType;

  typedef
    itk::Statistics::Histogram<HistogramMeasurementRealType, DFContainerType>
    HistogramType;

  typedef itk::VariableLengthVector< unsigned int > CountVectorType;

  typedef PixelType                                       MeasurementVectorType;
  typedef ObjectList<HistogramType>                       HistogramListType;
  typedef typename HistogramListType::Pointer             HistogramListPointerType;
  typedef typename std::vector<HistogramListPointerType>  ArrayHistogramListType;

  //manage mask
  typedef TMaskImage                                     MaskImageType;
  typedef typename MaskImageType::PixelType              MaskPixelType;

  /** Method to set/get the mask */
  //itkSetInputMacro(MaskImage, MaskImageType);
  virtual void SetMaskImage(const MaskImageType *_arg)                                       
    {                                                                                                     
    if ( _arg != itkDynamicCastInDebugMode< MaskImageType * >( this->itk::ProcessObject::GetInput("MaskImage") ) )  
      {                                                                           
      this->itk::ProcessObject::SetInput( "MaskImage", const_cast< MaskImageType * >( _arg ) );       
      this->Modified();                                                           
      }                                                                           
    }
  //itkGetInputMacro(MaskImage, MaskImageType);
  virtual const MaskImageType * GetMaskImage() const                                                                        
    {                                                                                                           
    itkDebugMacro( "returning input " << "MaskImage" <<  " of " <<  this->itk::ProcessObject::GetInput("MaskImage") );               
    return itkDynamicCastInDebugMode< const MaskImageType * >( this->itk::ProcessObject::GetInput("MaskImage") );                   
    }

  /** Set the pixel value treated as on in the mask.
   * Only pixels with this value will be added to the histogram.
   */
  //otbSetGetDecoratedInputMacro(MaskValue, MaskPixelType);                                                                
  virtual void SetMaskValueInput(const itk::SimpleDataObjectDecorator< MaskPixelType > *_arg)                                
    {                                                                                                         
    itkDebugMacro("setting input " << "MaskValue" << " to " << _arg);                                                     
    if ( _arg != itkDynamicCastInDebugMode< itk::SimpleDataObjectDecorator< MaskPixelType > * >( this->itk::ProcessObject::GetInput("MaskValue") ) ) 
      {                                                                                                       
      this->itk::ProcessObject::SetInput( "MaskValue", const_cast< itk::SimpleDataObjectDecorator< MaskPixelType > * >( _arg ) );      
      this->Modified();                                                                                       
      }                                                                                                       
    }                                                                                                         
  virtual void SetMaskValue(const MaskPixelType &_arg)                           
    {                                                                
    typedef itk::SimpleDataObjectDecorator< MaskPixelType > DecoratorType;         
    itkDebugMacro("setting input " << "MaskValue" << " to " << _arg);            
    const DecoratorType *oldInput =                                  
      itkDynamicCastInDebugMode< const DecoratorType * >(            
        this->itk::ProcessObject::GetInput("MaskValue") );                      
    if ( oldInput && oldInput->Get() == _arg )                       
      {                                                              
      return;                                                        
      }                                                              
    typename DecoratorType::Pointer newInput = DecoratorType::New(); 
    newInput->Set(_arg);                                             
    this->SetMaskValueInput(newInput);                                
    }

/** Set a decorated input. This defines the Set"name"() and Set"name"Input() method */
                                                               
  virtual const itk::SimpleDataObjectDecorator< MaskPixelType > * GetMaskValueInput() const                                                                 
    {                                                                                                                                        
    itkDebugMacro( "returning input " << "MaskValue" << " of " << this->itk::ProcessObject::GetInput("MaskValue") );                                             
    return itkDynamicCastInDebugMode< const itk::SimpleDataObjectDecorator< MaskPixelType > * >( this->itk::ProcessObject::GetInput("MaskValue") );                   
    }                                                                
  virtual const MaskPixelType & GetMaskValue() const                             
    {                                                                
    itkDebugMacro("Getting input " << "MaskValue");                           
    typedef itk::SimpleDataObjectDecorator< MaskPixelType > DecoratorType;         
    const DecoratorType *input =                                     
      itkDynamicCastInDebugMode< const DecoratorType * >(            
        this->itk::ProcessObject::GetInput("MaskValue") );                      
    if( input == ITK_NULLPTR )                                       
      {                                                              
      itkExceptionMacro(<<"input" << "MaskValue" << " is not set");              
      }                                                              
    return input->Get();                                             
    }
  ////////////
  /** Set the no data value. These value are ignored in histogram
   *  computation if NoDataFlag is On
   */
  itkSetMacro(NoDataValue, InternalPixelType);

  /** Set the no data value. These value are ignored in histogram
   *  computation if NoDataFlag is On
   */
  itkGetConstReferenceMacro(NoDataValue, InternalPixelType);

  /** Set the NoDataFlag. If set to true, samples with values equal to
   *  m_NoDataValue are ignored.
   */
  itkSetMacro(NoDataFlag, bool);

  /** Get the NoDataFlag. If set to true, samples with values equal to
   *  m_NoDataValue are ignored.
   */
  itkGetMacro(NoDataFlag, bool);

  /** Toggle the NoDataFlag. If set to true, samples with values equal to
   *  m_NoDataValue are ignored.
   */
  itkBooleanMacro(NoDataFlag);

  inline void SetNumberOfBins( unsigned int i, CountVectorType::ValueType size )
  {
    m_Size[ i ] = size;
  }

  inline void SetNumberOfBins( const CountVectorType& size )
  {
    m_Size = size;
  }

  /** Return the computed histogram list */
  HistogramListType* GetHistogramListOutput();
  const HistogramListType* GetHistogramListOutput() const;

  /** Get the minimum values for histograms */
  itkGetConstReferenceMacro(HistogramMin,MeasurementVectorType);

  /** Set the minimum values for histograms */
  itkSetMacro(HistogramMin,MeasurementVectorType);

  /** Get the maximum values for histograms */
  itkGetConstReferenceMacro(HistogramMax,MeasurementVectorType);

  /** Set the maximum values for histograms */
  itkSetMacro(HistogramMax,MeasurementVectorType);

  /** Set the subsampling rate */
  itkSetMacro(SubSamplingRate, unsigned int);

  /** Get the subsampling rate */
  itkGetMacro(SubSamplingRate, unsigned int);

  /** Make a DataObject of the correct type to be used as the specified
   * output.
   */
  virtual DataObjectPointer MakeOutput(DataObjectPointerArraySizeType idx);
  using Superclass::MakeOutput;

  /** Pass the input through unmodified. Do this by Grafting in the
   *  AllocateOutputs method.
   */
  virtual void AllocateOutputs();
  virtual void GenerateOutputInformation();
  virtual void Synthetize(void);
  virtual void Reset(void);

protected:
  PersistentHistogramMaskedVectorImageFilter();
  virtual ~PersistentHistogramMaskedVectorImageFilter() {}
  virtual void PrintSelf(std::ostream& os, itk::Indent indent) const;
  /** Multi-thread version GenerateData. */
  void  ThreadedGenerateData(const RegionType& outputRegionForThread, itk::ThreadIdType threadId);

private:
  PersistentHistogramMaskedVectorImageFilter(const Self &); //purposely not implemented
  void operator =(const Self&); //purposely not implemented

  ArrayHistogramListType   m_ThreadHistogramList;
  CountVectorType          m_Size;
  MeasurementVectorType    m_HistogramMin;
  MeasurementVectorType    m_HistogramMax;
  bool                     m_NoDataFlag;
  InternalPixelType        m_NoDataValue;

  /** Set the subsampling along each direction */
  unsigned int             m_SubSamplingRate;

}; // end of class PersistentStatisticsVectorImageFilter

/**===========================================================================*/

/** class StreamingHistogramMaskedVectorImageFilter
 * brief This class streams the whole input image through the PersistentHistogramMaskedVectorImageFilter.
 *
 * This way, it allows to compute the min/max of this image. It calls the
 * Reset() method of the PersistentHistogramMaskedVectorImageFilter before streaming the image and the
 * Synthetize() method of the PersistentHistogramMaskedVectorImageFilter after having streamed the image
 * to compute the statistics. The accessor on the results are wrapping the accessors of the
 * internal PersistentMinMaxImageFilter.
 *
 * sa PersistentStatisticsVectorImageFilter
 * sa PersistentImageFilter
 * sa PersistentFilterStreamingDecorator
 * sa StreamingImageVirtualWriter
 * ingroup Streamed
 * ingroup Multithreaded
 * ingroup MathematicalStatisticsImageFilters
 *
 * ingroup OTBStatistics
 */

template<class TInputImage, class TMaskImage>
class ITK_EXPORT StreamingHistogramMaskedVectorImageFilter :
  public PersistentFilterStreamingDecorator<PersistentHistogramMaskedVectorImageFilter<TInputImage, TMaskImage> >
{
public:
  /** Standard Self typedef */
  typedef StreamingHistogramMaskedVectorImageFilter   Self;
  typedef PersistentFilterStreamingDecorator
  <PersistentHistogramMaskedVectorImageFilter<TInputImage, TMaskImage> > Superclass;
  typedef itk::SmartPointer<Self>       Pointer;
  typedef itk::SmartPointer<const Self> ConstPointer;

  /** Type macro */
  itkNewMacro(Self);

  /** Creation through object factory macro */
  itkTypeMacro(StreamingHistogramMaskedVectorImageFilter, PersistentFilterStreamingDecorator);

  typedef TInputImage                                 InputImageType;	
  typedef TMaskImage                                  InputMaskType;
  
  typedef typename Superclass::FilterType             InternalFilterType;

  typedef typename InternalFilterType::MaskPixelType  MaskPixelType;
  /** Types needed for histograms */
  typedef typename InternalFilterType::HistogramType      HistogramType;
  typedef typename InternalFilterType::HistogramListType  HistogramListType;

  using Superclass::SetInput;
  void SetInput(InputImageType * input)
  {
    this->GetFilter()->SetInput(input);
  }
  const InputMaskType * GetMaskImage()
  {
    return this->GetFilter()->GetMaskImage();
  }

  void SetMaskImage(InputMaskType * input)
  {
    this->GetFilter()->SetMaskImage(input);
  }

  const MaskPixelType GetMaskValue()
  {
    return this->GetFilter()->GetMaskValue();
  }

  void SetMaskValue(MaskPixelType input)
  {
    this->GetFilter()->SetMaskValue(input);
  }
  const InputImageType * GetInput()
  {
    return this->GetFilter()->GetInput();
  }


  /** Return the computed histogram */
  HistogramListType* GetHistogramList()
  {
    return this->GetFilter()->GetHistogramListOutput();
  }


protected:
  /** Constructor */
  StreamingHistogramMaskedVectorImageFilter() {};
  /** Destructor */
  virtual ~StreamingHistogramMaskedVectorImageFilter() {}

private:
  StreamingHistogramMaskedVectorImageFilter(const Self &); //purposely not implemented
  void operator =(const Self&); //purposely not implemented
};

} // end namespace otb

#ifndef OTB_MANUAL_INSTANTIATION
#include "otbStreamingHistogramMaskedVectorImageFilter.txx"
#endif

#endif
