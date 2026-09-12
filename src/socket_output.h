#ifndef HAVEN_SOCKET_OUTPUT_H
#define HAVEN_SOCKET_OUTPUT_H
#include <algorithm>
#include <cerrno>
#include <cstring>
#include <cstdlib>
#include <sys/socket.h>
#include <unistd.h>

namespace haven {
struct SocketWrite { size_t sent; bool ok; };
inline SocketWrite write_socket(int fd, const char *bytes, size_t size) {
    size_t sent = 0;
    while (sent < size) {
        const ssize_t count = send(fd, bytes + sent, std::min(size - sent, size_t(4096)), MSG_NOSIGNAL);
        if (count < 0 && errno == EINTR) continue;
        if (count < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) return {sent, true};
        if (count <= 0) return {sent, false};
        sent += static_cast<size_t>(count);
    }
    return {sent, true};
}

// A stalled client retains at most 1 MiB. Disconnect on the next output pass,
// rather than freeing its descriptor in the middle of a gameplay callback.
inline void queue_socket_output(DESCRIPTOR_DATA *d, const char *bytes, size_t size) {
    const size_t limit = 1024 * 1024;
    if (d->out_overflow) return;
    if (size > limit || size_t(d->outtop) > limit - size) {
        d->out_overflow = true;
        return;
    }
    if (size_t(d->outtop) + size >= size_t(d->outsize)) {
        size_t capacity = d->outsize;
        while (size_t(d->outtop) + size >= capacity)
            capacity = std::min(capacity * 2, limit + 1);
        // Socket backlogs can exceed the engine allocator's largest bucket.
        char *buffer = static_cast<char *>(std::realloc(d->outbuf, capacity));
        if (!buffer) { d->out_overflow = true; return; }
        d->outbuf = buffer;
        d->outsize = capacity;
    }
    memcpy(d->outbuf + d->outtop, bytes, size);
    d->outtop += size;
    d->outbuf[d->outtop] = '\0';
}

inline bool flush_socket_output(DESCRIPTOR_DATA *d) {
    if (d->out_overflow) return false;
    // Bound work per player per pulse, even on a fast socket.
    const SocketWrite result = write_socket(d->descriptor, d->outbuf,
                                            std::min(size_t(d->outtop), size_t(64 * 1024)));
    d->outtop -= result.sent;
    d->out_prepared = std::max(0, d->out_prepared - int(result.sent));
    memmove(d->outbuf, d->outbuf + result.sent, d->outtop);
    d->outbuf[d->outtop] = '\0';
    return result.ok;
}
}
#endif
