#ifndef IN_MEMORY_SIGNAL_STORE_H_
#define IN_MEMORY_SIGNAL_STORE_H_

#include <vector>
#include <map>
#include <utility>
#include <deque>
#include <string>

#include "Store.h"
#include "rapidjson/document.h"

using namespace rapidjson;
namespace session {

class inMemorySignalStore : public Store<inMemorySignalStore>
{
  public:
    inMemorySignalStore();
    ~inMemorySignalStore() = default;

    // transform from a signal Json Record (i.e. a rapidJson Document) into a pair of uint64_t s and a string id
    template<typename signalJsonRecord>
    void ingressRecordsImpl    (std::vector<signalJsonRecord> ingressRecordVector)
    {
      for (auto element : ingressRecordVector)
      {
        assert(element.HasMember["Time"]);
        assert(element.HasMember["Signal_*"]);
        std::string elementName;
        // TODO(jjad) brittle, replace with iterator
        if (element[0].GetName() != std::string("Time"))
        {
          elementName = element[0].GetName();
        }
        else
        {
          elementName = element[1].GetName();
        }
        ingressStoreRecord(elementName, std::make_pair(static_cast<uint64_t>(std::stoi(element["Signal_*"].GetString())), static_cast<uint64_t>(std::stoi(element["Time"].GetString()))));
      }
    }

    // one of these will be spun up per signal egress required: the "id" will already be known
    std::vector<std::pair<uint64_t, uint64_t> >   egressRecordsImpl     (const std::string& id, uint64_t extractionNumber)
    {
      return egressStoreRecords(id, extractionNumber);
    }

  private:
    void                                          ingressStoreRecord    (const std::string& id, std::pair<uint64_t, uint64_t> valueTimePair);
    std::vector<std::pair<uint64_t, uint64_t>>    egressStoreRecords    (const std::string& id, uint64_t extractionNumber);
    std::map<std::string, std::deque< std::pair<uint64_t, uint64_t> > > _signalStore;
    // for stats reasons, and so the constructor has something to do
    uint32_t                                                            _channelCount;
    // C H O N K Y error stat
    uint64_t                                                            _recordsDropped;
};

}  // namespace session

#endif  // IN_MEMORY_SIGNAL_STORE_H_
