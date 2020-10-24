#ifndef STORE_H_
#define STORE_H_

#include <vector>
#include <utility>

namespace session {

// using a pImpl interface for the following reasons:
// separate concerns from rapidjson tomfoolery:
//  Binary Compatibility: The binary interface is independent of the private fields. Making changes to the implementation would not brake the dependent code.
//  Compilation time: Compilation time drops due to the fact that only the implementation file needs to be rebuilt instead of every client recompiling his file.
//  Data Hiding: Can easily hide certain internal details such as implementation techniques and other libraries used to implement the public interface.
template<typename specificSignalStore>
class Store
{
  public:
      virtual ~Store();
      template<typename signalJsonRecord>
      void                                                     ingressRecords           (std::vector<signalJsonRecord> ingressRecordVector)
      {
        impl_->ingressRecordsImpl(ingressRecordVector);
      }
      // method to be spun up once per channel type
      std::vector<std::pair<uint32_t, uint32_t> >              egressRecords            ()
      {
        return impl_->egressRecordsImpl();
      }
  protected:
     Store() :
       impl_(static_cast<specificSignalStore*>(this)) {
   }


  private:
      specificSignalStore* impl_;
};

} // namespace session
#endif  // STORE_H_
