#include "Note.h"
#include "merc.h"
#include "global.h"
#include "recycle.h"
#include "ai_protocol.h"
#include "social_lookup.h"
#include "socket_output.h"
#include "runtime_io.h"
#include <cassert>
#include <climits>
#include <fcntl.h>
#include <fstream>

extern "C" {
extern char *string_space, *top_string;
void social_update();
void ai_update();
void ai_minute();
void ai_operation_job();
void ai_social_score(MATCH_TYPE *);
void find_doom(CHAR_DATA *);
void create_ai_operative(CHAR_DATA *, int);
void run_ai_job(const std::string &);
void update_ai_operation(std::vector<std::string>);
bool process_output(DESCRIPTOR_DATA *, bool);
int __wrap_number_percent() { return 3; }
ssize_t __real_send(int, const void *, size_t, int);
}
static bool interrupt_send = false;
extern "C" ssize_t __wrap_send(int fd, const void *bytes, size_t size, int flags) {
    if (interrupt_send) { interrupt_send = false; errno = EINTR; return -1; }
    return __real_send(fd, bytes, size, flags);
}

class TextInput : public StaticInput {
    std::string text_;
public:
    explicit TextInput(std::string text) : text_(std::move(text)) {
        m_szData = m_pcStart = text_.c_str(); m_pcEnd = m_pcStart + text_.size();
    }
};
class TextOutput : public Output {
public:
    std::string text;
    TextOutput() { m_bActive = true; }
    void largewrite(const void *bytes, size_t length) override { text.append(static_cast<const char *>(bytes), length); }
    void flush() override { largewrite(m_szBuf, m_pcStart - m_szBuf); m_pcStart = m_szBuf; }
};

static void text_io() {
    TextOutput output;
    output.sendf("%09000d:%s", 1, "tail");
    output << ' ' << LONG_MIN << ' ' << ULONG_MAX;
    output.flush();
    assert(output.text == std::string(8999, '0') + "1:tail " + std::to_string(LONG_MIN) + " " + std::to_string(ULONG_MAX));
    char small[8];
    TextInput word("toolongword next");
    assert(word.getWord(small) == small && small[0] == 0 && word.failed());
    TextInput line("too long a line\n");
    line.getLine(small); assert(line.failed() && !small[0]);
    TextInput string("too long a string~ End");
    string.getString(small); assert(string.failed() && !small[0]);
    TextInput empty("");
    assert(empty.getWord(small) == small && !small[0]);
    TextInput quoted("'unfinished");
    quoted.getWord(small); assert(quoted.failed());
    TextInput normal("'a b' # `%%~");
    assert(normal.getWord() == "a b" && normal.getWord() == "#" && normal.getString() == "`W%");

    NoteBoard board;
    TextInput board_input("Name board~\nDisplay " + std::string(1100, 'x') + "~\nEnd\n");
    assert(board.readFrom(board_input) && board.getDisplay() == std::string(1100, 'x'));
    TextInput bad_board("Display missing terminator");
    assert(!board.readFrom(bad_board));
    Note note;
    TextInput note_input("Text\n" + std::string(40000, 'a') + "\nsecond line~\nEnd\n");
    assert(note.readFrom(note_input));
    assert(note.getText() == std::string(40000, 'a') + "\n\rsecond line");
    TextInput bad_note("Text valid~\n");
    assert(!note.readFrom(bad_note));
    puts("PASS: long formatted output, integer extremes, bounded readers, long notes and truncated records.");
}

static void socket_output() {
    int sockets[2]; assert(socketpair(AF_UNIX, SOCK_STREAM, 0, sockets) == 0);
    int size = 4096; assert(setsockopt(sockets[0], SOL_SOCKET, SO_SNDBUF, &size, sizeof(size)) == 0);
    assert(fcntl(sockets[0], F_SETFL, O_NONBLOCK) == 0);
    assert(fcntl(sockets[1], F_SETFL, O_NONBLOCK) == 0);
    DESCRIPTOR_DATA *d = new_descriptor();
    assert(d->outbuf[0] == '\0');
    DESCRIPTOR_DATA *snoop = new_descriptor();
    d->snoop_by = snoop;
    d->descriptor = sockets[0];
    d->showstr_point = const_cast<char *>("pager");
    std::string original(300000, 'x'); original[1500] = '\0';
    haven::queue_socket_output(d, original.data(), original.size());
    interrupt_send = true;
    assert(process_output(d, true) && d->outtop > 0);
    std::string expected = original + "[Hit Return to continue]\n\r";
    const std::string late = "\nnew output";
    haven::queue_socket_output(d, late.data(), late.size());
    assert(process_output(d, true));
    const std::string snooped = "# " + expected + "# " + late + "[Hit Return to continue]\n\r";
    expected += late + "[Hit Return to continue]\n\r";
    std::string received;
    auto drain = [&]() {
        char buffer[4096]; ssize_t bytes;
        while ((bytes = recv(sockets[1], buffer, sizeof(buffer), 0)) > 0) received.append(buffer, bytes);
        assert(errno == EAGAIN || errno == EWOULDBLOCK);
    };
    for (int i = 0; d->outtop && i < 1000; ++i) {
        drain();
        assert(process_output(d, true));
    }
    drain();
    assert(d->outtop == 0 && d->out_prepared == 0 && received == expected);
    assert(d->outbuf[0] == '\0');
    assert(std::string(snoop->outbuf, snoop->outtop) == snooped);
    d->snoop_by = nullptr;
    free_descriptor(snoop);
    d->showstr_point = nullptr;
    close(sockets[1]);
    haven::queue_socket_output(d, "closed", 6);
    assert(!haven::flush_socket_output(d)); // EPIPE must not raise SIGPIPE.
    close(sockets[0]);
    d->outtop = 0;
    haven::queue_socket_output(d, original.data(), 1024 * 1024 + 1);
    assert(d->out_overflow && !process_output(d, false));
    free_descriptor(d);
    puts("PASS: socket backpressure/EINTR, byte-exact delivery, no duplicate prompts/snooping, EPIPE and bounded backlog.");
}

static void social_matching() {
    PROFILE_TYPE first = {}, duplicate = {};
    first.name = const_cast<char *>("Alice"); duplicate.name = const_cast<char *>("ALICE");
    MATCH_TYPE one = {}, two = {};
    one.nameone = const_cast<char *>("Alice"); one.nametwo = const_cast<char *>("Bob");
    two.nameone = const_cast<char *>("BOB"); two.nametwo = const_cast<char *>("ALICE");
    ProfileVect = {&first, &duplicate}; MatchVect = {&one, &two};
    {
        haven::SocialLookup lookup(ProfileVect, MatchVect);
        assert(lookup.profile("aLiCe") == &first && !lookup.profile("missing"));
        assert(lookup.match("bob", "alice") == &one && !lookup.match("alice", "missing"));
    }
    std::reverse(ProfileVect.begin(), ProfileVect.end());
    haven::SocialLookup refreshed(ProfileVect, MatchVect);
    assert(refreshed.profile("alice") == &duplicate);
    current_time = 2000000000;
    one.chat_initiatior = 1; two.chat_initiatior = 2;
    one.last_chat_when = two.last_chat_when = current_time - 4 * 3600;
    one.last_msg_one_one = two.last_msg_two_one = current_time - 3600;
    one.last_msg_two_one = two.last_msg_one_one = current_time - 5 * 3600;
    social_update(); social_update();
    assert(one.success_chat_one == 1 && one.failed_chat_two == 1 && one.chat_initiatior == 0);
    assert(two.success_chat_two == 1 && two.failed_chat_one == 1 && two.chat_initiatior == 0);
    ProfileVect.clear(); MatchVect.clear();
    puts("PASS: case-insensitive social indexes, duplicate order, refresh after reordering and exactly one invitation outcome.");
}

static void ai_results() {
    unsetenv("HAVEN_ENABLE_AI");
    assert(!haven::ai_enabled());
    for (const char *value : {"", "0", "true", "yes"}) {
        setenv("HAVEN_ENABLE_AI", value, 1);
        assert(!haven::ai_enabled());
    }
    unsetenv("HAVEN_ENABLE_AI");
    for (const char *path : {"ai_in.csv", "ai_sum_in.csv", "ai_out.csv", "ai_sum_out.csv"}) {
        { std::ofstream queue(path); queue << "pending\n"; }
        assert(!haven::append_file_bytes(path, "new\n"));
        assert(haven::pop_file_line(path).empty());
        assert(access((std::string(path) + ".cursor").c_str(), F_OK) != 0);
        assert(access((std::string(path) + ".lock").c_str(), F_OK) != 0);
        std::ifstream queue(path);
        assert(std::string(std::istreambuf_iterator<char>(queue), {}) == "pending\n");
        unlink(path);
    }
    // Disabled jobs return before looking up characters, factions, or histories.
    ai_update(); ai_minute(); ai_operation_job(); ai_social_score(nullptr); find_doom(nullptr);
    CHAR_DATA applicant = {}; PC_DATA applicant_data = {};
    DESCRIPTOR_DATA *descriptor = new_descriptor();
    applicant.pcdata = &applicant_data; applicant.desc = descriptor;
    descriptor->character = &applicant; descriptor->host = str_dup("test");
    create_ai_operative(&applicant, FACTION_CORE);
    assert(applicant_data.operative_creation_faction == 0);
    assert(descriptor->outbuf && strstr(descriptor->outbuf, "disabled")); free_descriptor(descriptor);
    MATCH_TYPE untouched = {}; untouched.nameone = (char *)"Alice"; untouched.nametwo = (char *)"Bob";
    MatchVect = {&untouched};
    run_ai_job("[4,\"Alice\",20,\"Bob\",30,\"review\"]");
    assert(untouched.score_one_auto_chat == 0 && untouched.score_two_auto_chat == 0);
    MatchVect.clear();
    setenv("HAVEN_ENABLE_AI", "1", 1);
    assert(haven::ai_enabled());
    std::vector<std::string> fields;
    for (const char *bad : {"", "1", "4|||Alice|||20|||Bob|||bad|||review", "[1]", "[1,1,null]",
                           "[1,1,\"bad\\u0000value\"]", "3|||../Alice|||1|||text", "3|||Alice|||999999999999999999999|||text"}) {
        assert(!haven::parse_ai_record(bad, fields));
        run_ai_job(bad); // Actual dispatcher must reject safely, too.
    }
    assert(haven::parse_ai_record("[6,\"Alice\",\"Bob\",\"Smith\",\"person\",\"line1\\nline2 ||| \\\"quote\\\"\",\"black\",\"blue\",6,1,\"pale\"]", fields));
    assert(fields[5] == "line1\nline2 ||| \"quote\"");
    MATCH_TYPE match = {};
    match.nameone = const_cast<char *>("Alice"); match.nametwo = const_cast<char *>("Bob"); MatchVect = {&match};
    run_ai_job("4|||Alice|||20|||Bob|||bad|||review");
    assert(match.score_one_auto_chat == 0 && match.score_two_auto_chat == 0);
    run_ai_job("[4,\"Alice\",20,\"Bob\",30,\"review\"]");
    assert(match.score_one_auto_chat == 20 && match.score_two_auto_chat == 30);
    free_string(match.auto_chat_review); MatchVect.clear();
    FACTION_TYPE faction = {}; faction.vnum = 71; faction.name = const_cast<char *>("Antagonist"); faction.antagonist = 1;
    FacVect = {&faction}; invalidate_faction_index();
    OPERATION_TYPE one = {}, two = {}, orphan = {};
    for (auto *op : {&one, &two, &orphan}) {
        op->valid = true; op->faction = 71; op->description = str_dup("");
        op->room_name = str_dup(""); op->upload_name = str_dup("");
    }
    one.territoryvnum = 100; two.territoryvnum = 200; orphan.faction = 999;
    OpVect = {nullptr, &orphan, &one, &two};
    std::vector<std::string> operation = {"2", "Antagonist", "field", "Room", "Process", "A complete description"};
    update_ai_operation(operation);
    assert(!strlen(one.description) && !strlen(two.description));
    operation.insert(operation.end(), {"200", "71", "0"});
    update_ai_operation(operation);
    assert(!strlen(one.description) && !strcmp(two.description, "A complete description"));
    update_ai_operation(operation);
    assert(!strlen(one.description));
    for (auto *op : {&one, &two, &orphan}) {
        free_string(op->description); free_string(op->room_name); free_string(op->upload_name);
    }
    OpVect.clear(); FacVect.clear(); invalidate_faction_index();
    assert(haven::append_ai_summary("ai_sum_in.csv", 1, 0, "title~quoted", "line1\nline2~end"));
    std::ifstream file("ai_sum_in.csv");
    std::string content(std::istreambuf_iterator<char>(file), {});
    assert(content == "type,subtype,title,text\n1,0,~title~~quoted~,~line1\nline2~~end~\n");
    unsetenv("HAVEN_ENABLE_AI");
    puts("PASS: default-off AI preserves queues and gameplay; opt-in restores processing. Malformed AI records rejected before mutation, JSON/legacy framing, operation identity and atomic summary records.");
}

int main() {
    char pool[] = "pool"; string_space = pool; top_string = pool + sizeof(pool);
    text_io(); socket_output(); social_matching(); ai_results();
}
