#include "merc.h"
#include <cerrno>
#include <cstring>
#if !defined(WIN32)
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

extern "C" {
_DOFUN(do_gameupdate) {
    // Also enforce this here: command files, force and direct calls can bypass
    // the normal command table's trust check.
    if (IS_NPC(ch) || !IS_ADMIN(ch)) {
        send_to_char("Only admins may use gameupdate.\n\r", ch);
        return;
    }
#if defined(WIN32)
    send_to_char("Game updates require the Linux server build.\n\r", ch);
#else
    char action[MAX_INPUT_LENGTH];
    argument = one_argument(argument, action);
    if (*argument || (str_cmp(action, "build") && str_cmp(action, "status") &&
                     str_cmp(action, "log") && str_cmp(action, "install") &&
                     str_cmp(action, "rollback"))) {
        send_to_char("Gameupdate build | status | log | install | rollback\n\r"
                     "Build downloads and compiles separately. Install replaces only the executable.\n\r"
                     "After installation, use copyover now when ready.\n\r", ch);
        return;
    }
    struct stat st;
    if (mkdir("../.updates", 0700) < 0 && errno != EEXIST) {
        send_to_char("Cannot create ../.updates; check server permissions.\n\r", ch);
        return;
    }
    if (lstat("../.updates", &st) < 0 || !S_ISDIR(st.st_mode)) {
        send_to_char("../.updates must be a real directory, not a symlink.\n\r", ch);
        return;
    }
    if (!str_cmp(action, "status") || !str_cmp(action, "log")) {
        int lockfd = open("../.updates/lock", O_RDWR | O_CREAT | O_NOFOLLOW, 0600);
        if (lockfd >= 0) {
            if (flock(lockfd, LOCK_EX | LOCK_NB) < 0)
                send_to_char("An update operation is running.\n\r", ch);
            else
                send_to_char("Updater idle. Any RUNNING message below is from an interrupted operation.\n\r", ch);
            close(lockfd);
        }
        const char *path = !str_cmp(action, "log") ? "../.updates/update.log" : "../.updates/status.txt";
        FILE *fp = fopen(path, "r");
        if (!fp) {
            send_to_char("No update output yet.\n\r", ch);
            return;
        }
        char output[4097];
        if (!str_cmp(action, "log")) {
            fseek(fp, 0, SEEK_END);
            long size = ftell(fp);
            fseek(fp, size > 4096 ? size - 4096 : 0, SEEK_SET);
        }
        size_t count = fread(output, 1, sizeof(output) - 1, fp);
        output[count] = '\0';
        fclose(fp);
        send_to_char(output, ch);
        send_to_char("\n\r", ch);
        return;
    }
    if (access("../tools/game_update.py", R_OK) != 0) {
        send_to_char("Missing ../tools/game_update.py; install the updater helper first.\n\r", ch);
        return;
    }
    int logfd = open("../.updates/update.log", O_WRONLY | O_CREAT | O_APPEND | O_NOFOLLOW, 0600);
    if (logfd < 0) {
        send_to_char("Cannot open the updater log.\n\r", ch);
        return;
    }
    long maxfd = sysconf(_SC_OPEN_MAX);
    if (maxfd < 0) {
        close(logfd);
        send_to_char("Cannot determine descriptor limit; update aborted.\n\r", ch);
        return;
    }
    pid_t pid = fork();
    if (pid == 0) {
        setsid();
        dup2(logfd, STDOUT_FILENO);
        dup2(logfd, STDERR_FILENO);
        close(STDIN_FILENO);
        open("/dev/null", O_RDONLY);
        // Do not let the build retain listening sockets or player connections.
        for (long fd = 3; fd < maxfd; ++fd)
            close(static_cast<int>(fd));
        execlp("python3", "python3", "../tools/game_update.py", action, (char *)NULL);
        perror("Unable to launch game updater (python3 required)");
        _exit(127);
    }
    close(logfd);
    if (pid < 0) {
        send_to_char("Unable to start the update worker.\n\r", ch);
        return;
    }
    printf_to_char(ch, "Update %s requested. Check gameupdate status and gameupdate log.\n\r", action);
#endif
}
}
