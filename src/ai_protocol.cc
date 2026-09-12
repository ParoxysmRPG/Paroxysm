#include "ai_protocol.h"
#include "rapidjson/rapidjson/document.h"

bool haven::parse_ai_record(const std::string &input, std::vector<std::string> &fields) {
    fields.clear();
    // JSON escaping can expand a valid field by six bytes per input byte.
    if (input.empty() || input.size() > 2 * 1024 * 1024) return false;
    const size_t first = input.find_first_not_of(" \t\r\n");
    if (first != std::string::npos && input[first] == '[') {
        rapidjson::Document doc;
        doc.Parse(input.data(), input.size());
        if (doc.HasParseError() || !doc.IsArray() || doc.Size() > 11) return false;
        for (const auto &value : doc.GetArray()) {
            if (value.IsString()) fields.emplace_back(value.GetString(), value.GetStringLength());
            else if (value.IsInt()) fields.push_back(std::to_string(value.GetInt()));
            else return false;
        }
    } else {
        // Drain existing producer queues during migration.
        size_t start = 0;
        while (true) {
            const size_t end = input.find("|||", start);
            fields.push_back(input.substr(start, end == std::string::npos ? end : end - start));
            if (fields.size() > 11) return false;
            if (end == std::string::npos) break;
            start = end + 3;
        }
    }
    return valid_ai_fields(fields);
}
