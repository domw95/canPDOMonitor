#include <algorithm>
#include <iostream>

#include "inMemorySignalStore.h"

namespace session
{

//
// Public
//

inMemorySignalStore::inMemorySignalStore() :
    _channelCount(0),
    _recordsDropped(0)
{
}

//
// Private
//

void inMemorySignalStore::ingressStoreRecord(const std::string& id, std::pair<uint64_t, uint64_t> valueTimePair)
{
  auto record = _signalStore.find(id);
  if (_signalStore.end() != record)
  {
    record->second.push_front(valueTimePair);
  }
  else
  {
    std::deque<std::pair<uint64_t, uint64_t>> d;
    d.push_front(valueTimePair);
    _signalStore.insert(std::make_pair(id,d));
  }
}

std::vector<std::pair<uint64_t, uint64_t>>  inMemorySignalStore::egressStoreRecords(const std::string& id, uint64_t extractionNumber)
{
  std::vector<std::pair<uint64_t, uint64_t>> records;


  auto signalElement = _signalStore.find(id);
  if (signalElement != _signalStore.end())
  {
    if (signalElement->second.size() <= extractionNumber)
    {
      records.reserve(extractionNumber);
      uint64_t count = 0;
      while (count < extractionNumber)
      {
        records.push_back(signalElement->second.back());
        signalElement->second.pop_back();
        extractionNumber++;
      }
    }
    else
    {
      records.reserve(signalElement->second.size());
      uint64_t count = 0;
      while (count < signalElement->second.size())
      {
        records.push_back(signalElement->second.back());
        signalElement->second.pop_back();
        extractionNumber++;
      }
    }
  }
  else
  {
    std::cerr << "inMemorySignalStore Error: requested record " << id << " does not exist in store" << std::endl;
    _recordsDropped++;
  }
  return records;
}

}  // namespace session
