#include "runtime_io.h"
#include "merc.h"
#include <algorithm>
#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <map>
#include <memory>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>
#include <fstream>
#include <sstream>
#include <spawn.h>
#include <sys/wait.h>

extern char **environ;

bool haven::ai_enabled() {
    const char *enabled = std::getenv("HAVEN_ENABLE_AI");
    return enabled && std::strcmp(enabled, "1") == 0;
}

static bool disabled_ai_queue(const std::string &path) {
    const std::string name = path.substr(path.find_last_of("/\\") + 1);
    return (name == "ai_in.csv" || name == "ai_sum_in.csv" ||
            name == "ai_out.csv" || name == "ai_sum_out.csv" || name == "ai_sum_out.tmp") && !haven::ai_enabled();
}

bool haven::append_file_bytes(const std::string &path, const std::string &bytes) {
    if (disabled_ai_queue(path)) return false;
    int lock = open((path + ".lock").c_str(), O_CREAT | O_RDWR, 0600);
    if (lock < 0) return false;
    int result;
    do { result = flock(lock, LOCK_EX); } while (result < 0 && errno == EINTR);
    if (result < 0) { close(lock); return false; }
    int fd = open(path.c_str(), O_WRONLY | O_CREAT | O_APPEND, 0600);
    bool ok = fd >= 0;
    // Restore the original length on a failed partial append while still locked.
    const off_t start = ok ? lseek(fd, 0, SEEK_END) : -1;
    if (start < 0) ok = false;
    std::string record;
    if (start == 0) {
        const std::string name = path.substr(path.find_last_of('/') + 1);
        if (name == "ai_in.csv") record = "Type,ID,ValOne,ValTwo,ValThree,ValFour,ValFive\n";
        else if (name == "ai_sum_in.csv") record = "type,subtype,title,text\n";
    }
    record += bytes;
    size_t offset = 0;
    while (ok && offset < record.size()) {
        ssize_t written = write(fd, record.data() + offset, record.size() - offset);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) { ok = false; break; }
        offset += written;
    }
    if (ok) ok = fsync(fd) == 0;
    if (!ok && fd >= 0 && start >= 0) {
        if (ftruncate(fd, start) != 0 || fsync(fd) != 0)
            bugf("Unable to restore incomplete queue append: %s", path.c_str());
    }
    if (fd >= 0 && close(fd) != 0) ok = false;
    if (ok && start == 0) {
        const size_t slash = path.find_last_of('/');
        const std::string directory = slash == std::string::npos ? "." : path.substr(0, slash);
        int parent = open(directory.c_str(), O_RDONLY | O_DIRECTORY);
        if (parent < 0) ok = false;
        else { if (fsync(parent) != 0) ok = false; close(parent); }
    }
    flock(lock, LOCK_UN);
    close(lock);
    return ok;
}

bool haven::append_ai_summary(const std::string &path, int type, int subtype,
                              const char *title, const std::string &body) {
    if (!ai_enabled()) return false;
    auto quoted = [](const std::string &value) {
        std::string result = "~";
        for (char ch : value) { result += ch; if (ch == '~') result += '~'; }
        return result + "~";
    };
    return append_file_bytes(path, std::to_string(type) + "," + std::to_string(subtype) +
                             "," + quoted(title ? title : "") + "," + quoted(body) + "\n");
}

bool haven::remove_optional_file(const std::string &path) {
    if (std::remove(path.c_str()) == 0 || errno == ENOENT) return true;
    perror(path.c_str());
    return false;
}

bool haven::decompress_player_file(const std::string &path) {
    pid_t child;
    char *args[] = {const_cast<char *>("gzip"), const_cast<char *>("-dfq"),
                   const_cast<char *>("--"), const_cast<char *>(path.c_str()), nullptr};
    const int error = posix_spawnp(&child, "gzip", nullptr, nullptr, args, environ);
    if (error != 0) {
        errno = error;
        perror("Cannot start gzip");
        return false;
    }
    int status;
    pid_t waited;
    do { waited = waitpid(child, &status, 0); } while (waited < 0 && errno == EINTR);
    if (waited < 0) {
        perror("Cannot wait for gzip");
        return false;
    }
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0) {
        fprintf(stderr, "Cannot decompress player file: %s\n", path.c_str());
        return false;
    }
    return true;
}

namespace {
struct Snapshot {
    std::string path;
    char *bytes = nullptr;
    size_t size = 0;
    ~Snapshot() { std::free(bytes); }
};
std::map<FILE *, std::unique_ptr<Snapshot>> snapshots;

bool same_contents(const char *path, const char *bytes, size_t size) {
    FILE *file = fopen(path, "rb");
    if (!file) return false;
    char block[8192];
    size_t offset = 0;
    bool same = true;
    while (offset < size) {
        const size_t wanted = std::min(sizeof(block), size - offset);
        if (fread(block, 1, wanted, file) != wanted ||
            memcmp(block, bytes + offset, wanted) != 0) {
            same = false;
            break;
        }
        offset += wanted;
    }
    if (same) same = fgetc(file) == EOF && !ferror(file);
    fclose(file);
    return same;
}

// Same-directory rename keeps readers from seeing a partial save. On failure,
// leave the original intact and remove only our own temporary file.
bool replace_contents(const std::string &path, const char *bytes, size_t size) {
    std::string pattern = path + ".tmp.XXXXXX";
    std::vector<char> temporary(pattern.begin(), pattern.end());
    temporary.push_back('\0');
    int fd = mkstemp(temporary.data());
    if (fd < 0) return false;
    struct stat original;
    bool ok = true;
    if (stat(path.c_str(), &original) == 0)
        ok = fchmod(fd, original.st_mode & 0777) == 0;
    size_t offset = 0;
    while (ok && offset < size) {
        ssize_t written = write(fd, bytes + offset, size - offset);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) { ok = false; break; }
        offset += static_cast<size_t>(written);
    }
    if (ok && fsync(fd) != 0) ok = false;
    if (close(fd) != 0) ok = false;
    if (ok) ok = rename(temporary.data(), path.c_str()) == 0;
    if (ok) {
        const size_t slash = path.find_last_of('/');
        std::string directory = slash == std::string::npos ? "." : path.substr(0, slash);
        int parent = open(directory.c_str(), O_RDONLY | O_DIRECTORY);
        if (parent < 0) ok = false;
        else { if (fsync(parent) != 0) ok = false; close(parent); }
    }
    if (!ok) unlink(temporary.data());
    return ok;
}

class QueueLock {
    int fd_;
public:
    explicit QueueLock(const std::string &path)
        : fd_(open((path + ".lock").c_str(), O_CREAT | O_RDWR, 0600)) {
        // A busy writer must never stall the game loop; retry next pulse.
        if (fd_ >= 0 && flock(fd_, LOCK_EX | LOCK_NB) != 0) {
            close(fd_);
            fd_ = -1;
        }
    }
    ~QueueLock() { if (fd_ >= 0) { flock(fd_, LOCK_UN); close(fd_); } }
    bool acquired() const { return fd_ >= 0; }
};
}

extern "C" FILE *open_snapshot_file(const char *path) {
    std::unique_ptr<Snapshot> snapshot(new Snapshot);
    snapshot->path = path;
    FILE *stream = open_memstream(&snapshot->bytes, &snapshot->size);
    if (stream) snapshots.emplace(stream, std::move(snapshot));
    return stream;
}

extern "C" int close_snapshot_file_with_backup(FILE *stream, const char *backup) {
    auto found = snapshots.find(stream);
    if (found == snapshots.end()) return fclose(stream);
    std::unique_ptr<Snapshot> snapshot = std::move(found->second);
    snapshots.erase(found);
    const bool failed = ferror(stream) != 0;
    const int closed = fclose(stream);
    bool ok = !failed && closed == 0;
    if (ok) {
        // Attempt the backup even when saving the primary fails, as before.
        for (const char *path : {snapshot->path.c_str(), backup}) {
            if (!path) continue;
            if (!same_contents(path, snapshot->bytes, snapshot->size) &&
                !replace_contents(path, snapshot->bytes, snapshot->size)) {
                bugf("Unable to save snapshot: %s", path);
                ok = false;
            }
        }
    } else {
        bugf("Unable to serialize snapshot: %s", snapshot->path.c_str());
    }
    return ok ? 0 : EOF;
}

extern "C" int close_snapshot_file(FILE *stream) {
    return close_snapshot_file_with_backup(stream, nullptr);
}

namespace haven {
static const std::string death_journal = std::string(PLAYER_DIR) + ".death-recovery-journal";

bool replay_death_snapshots() {
    std::ifstream file(death_journal, std::ios::binary);
    if (!file) return access(death_journal.c_str(), F_OK) != 0 && errno == ENOENT;
    std::string path;
    size_t player_size, ground_size;
    if (!std::getline(file, path) || !(file >> player_size >> ground_size) || file.get() != '\n')
        return false;
    const std::string prefix = PLAYER_DIR;
    if (path.compare(0, prefix.size(), prefix) != 0 || path.size() == prefix.size()
        || path.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz", prefix.size()) != std::string::npos)
        return false;
    const std::streampos payload = file.tellg();
    file.seekg(0, std::ios::end);
    const std::streamoff remaining = file.tellg() - payload;
    if (remaining < 0 || player_size == 0 || ground_size == 0
        || player_size > static_cast<size_t>(remaining)
        || ground_size != static_cast<size_t>(remaining) - player_size) return false;
    file.seekg(payload);
    std::string player(player_size, '\0'), ground(ground_size, '\0');
    if (!file.read(&player[0], player_size) || !file.read(&ground[0], ground_size)
        || file.peek() != EOF) return false;
    if (!replace_contents(path, player.data(), player.size())
        || !replace_contents(std::string(PLAYER_DIR) + "GroundObjects", ground.data(), ground.size()))
        return false;
    if (unlink(death_journal.c_str()) != 0) return false;
    int parent = open(PLAYER_DIR, O_RDONLY | O_DIRECTORY);
    if (parent < 0) return false;
    bool ok = fsync(parent) == 0;
    close(parent);
    return ok;
}

bool commit_death_snapshots(const std::string &path, const std::string &player,
                            const std::string &ground) {
    if (!replay_death_snapshots()) return false;
    const std::string transaction = path + "\n" + std::to_string(player.size()) + " "
                                  + std::to_string(ground.size()) + "\n" + player + ground;
    if (!replace_contents(death_journal, transaction.data(), transaction.size())) return false;
    return replay_death_snapshots();
}

bool ensure_backup_directories() {
    bool ok = true;
    for (const char *root : {"../data/", ACCOUNT_DIR, PLAYER_DIR}) {
        for (int slot = 1; slot <= 7; ++slot) {
            const std::string path = std::string(root) + "back" + std::to_string(slot);
            if (mkdir(path.c_str(), 0700) == 0) continue;
            int error = errno;
            struct stat info;
            if (error == EEXIST && stat(path.c_str(), &info) == 0 && S_ISDIR(info.st_mode))
                continue;
            bugf("Unable to create backup directory %s: %s", path.c_str(), strerror(error));
            ok = false;
        }
    }
    return ok;
}

std::string pop_file_line(const std::string &path) {
    if (disabled_ai_queue(path)) return {};
    QueueLock lock(path);
    if (!lock.acquired()) return "";
    FILE *input = fopen(path.c_str(), "rb");
    if (!input) {
        if (errno != ENOENT) bugf("Unable to read AI queue: %s", path.c_str());
        return "";
    }
    struct stat info;
    if (fstat(fileno(input), &info) != 0) { fclose(input); return ""; }
    const std::string cursor_path = path + ".cursor";
    unsigned long long device = 0, inode = 0, consumed = 0;
    FILE *cursor = fopen(cursor_path.c_str(), "r");
    if (cursor) {
        const bool valid = fscanf(cursor, "%llu %llu %llu", &device, &inode, &consumed) == 3;
        fclose(cursor);
        if (!valid) {
            bugf("Invalid AI queue cursor: %s", cursor_path.c_str());
            fclose(input);
            return "";
        }
    } else if (errno != ENOENT) {
        fclose(input);
        return "";
    }
    // A replacement/compaction has a new inode and starts at byte zero.
    if (device != static_cast<unsigned long long>(info.st_dev)
        || inode != static_cast<unsigned long long>(info.st_ino)
        || consumed > static_cast<unsigned long long>(info.st_size)) consumed = 0;
    if (fseeko(input, static_cast<off_t>(consumed), SEEK_SET) != 0) {
        fclose(input);
        return "";
    }
    char *record = nullptr;
    size_t capacity = 0;
    const ssize_t length = getline(&record, &capacity, input);
    const bool complete = length > 0 && record[length - 1] == '\n' && !ferror(input);
    if (!complete) {
        free(record);
        fclose(input);
        return ""; // A partial record still belongs to the producer.
    }
    std::string line(record, static_cast<size_t>(length - 1));
    free(record);
    consumed += static_cast<unsigned long long>(length);
    const std::string position = std::to_string(info.st_dev) + " "
        + std::to_string(info.st_ino) + " " + std::to_string(consumed) + "\n";
    // Persist the input before the acknowledgement, including producer appends.
    if (fsync(fileno(input)) != 0
        || !replace_contents(cursor_path, position.data(), position.size())) {
        bugf("Unable to advance AI queue: %s", path.c_str());
        fclose(input);
        return "";
    }
    // Amortize copying: compact only after consuming at least 1 MiB and half
    // the file. Commit the old-inode cursor first. After atomic replacement,
    // even a restart before another cursor write reads the suffix from zero.
    if (consumed >= 1024 * 1024
        && consumed >= static_cast<unsigned long long>(info.st_size) / 2) {
        std::string remaining;
        char block[8192];
        size_t count;
        while ((count = fread(block, 1, sizeof(block), input)) != 0)
            remaining.append(block, count);
        if (ferror(input)
            || !replace_contents(path, remaining.data(), remaining.size()))
            bugf("Unable to compact AI queue: %s", path.c_str());
    }
    fclose(input);
    if (!line.empty() && line.back() == '\r') line.pop_back();
    return line;
}
}
