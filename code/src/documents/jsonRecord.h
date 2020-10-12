#ifndef json_RECORD_H_
#define json_RECORD_H_

#include "rapidjson/document.h"

class jsonRecord
{
  public:
    jsonRecord();
    ~jsonRecord();

   inline rapidjson::Document makeRecord()
   {
     const char* json = "{\"project\":\"rapidjson\",\"Time\":0.934,\"Signal_0\":-0.36187707387757756}";
     rapidjson::Document d;
     d.Parse(json);
     return d;
   };
};

#endif  // json_RECORD_H_
