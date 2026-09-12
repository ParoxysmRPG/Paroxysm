#ifndef HAVEN_REPORT_TEXT_H
#define HAVEN_REPORT_TEXT_H

// Append to a str_dup/fread_string-owned report. The result remains compatible
// with free_string and the existing char* readers and serializers.
extern "C" void append_report_text(char *&text, const char *suffix,
                                   bool newline = false);

#endif
