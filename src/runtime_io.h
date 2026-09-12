#ifndef HAVEN_RUNTIME_IO_H
#define HAVEN_RUNTIME_IO_H
#include <cstdio>
#include <string>

// Serialize to memory, then replace the destination only if its bytes changed.
extern "C" FILE *open_snapshot_file(const char *path);
extern "C" int close_snapshot_file(FILE *stream);
// Commit the same serialized bytes to both paths, attempting each independently.
extern "C" int close_snapshot_file_with_backup(FILE *stream, const char *backup);

namespace haven {
// Opt in explicitly in both the game and worker environments. Default is off.
bool ai_enabled();
// Append a complete record under the stable producer/consumer lock.
bool append_file_bytes(const std::string &path, const std::string &bytes);
bool append_ai_summary(const std::string &path, int type, int subtype,
                       const char *title, const std::string &body);
// File names are passed directly to the OS, never interpreted by a shell.
bool remove_optional_file(const std::string &path);
bool decompress_player_file(const std::string &path);
// Create the seven rotating backup directories under each existing save root.
bool ensure_backup_directories();
// A death moves ownership between two save files. Replay a prepared transaction
// before loading either file after a restart.
bool commit_death_snapshots(const std::string &player_path,
                            const std::string &player, const std::string &ground);
bool replay_death_snapshots();
// Durable read cursor and occasional compaction. Producers must append while
// holding <path>.lock and reopen the path for each append (compaction renames).
// The cursor is tied to the local inode; export the unread suffix for migration.
std::string pop_file_line(const std::string &path);
}
#endif
