#include "merc.h"
#include "global.h"
#include "recycle.h"
#include <cassert>
#include <fstream>
#include <string>

extern "C" {
extern char *string_space, *top_string;
extern int num_descriptors;
void state_confirm_new_account_name(DESCRIPTOR_DATA *, char *, ACCOUNT_TYPE *);
void state_get_new_account_password(DESCRIPTOR_DATA *, char *, ACCOUNT_TYPE *);
void state_confirm_new_account_password(DESCRIPTOR_DATA *, char *, ACCOUNT_TYPE *);
void state_get_old_account_password(DESCRIPTOR_DATA *, char *, ACCOUNT_TYPE *);
void state_get_old_password(DESCRIPTOR_DATA *, char *, CHAR_DATA *);
}

static char password[] = "LoginSecret73";
static char wrong[] = "WrongSecret84";
static const std::string echo_off("\xff\xfb\x01", 3);
static const std::string echo_on("\xff\xfc\x01", 3);

struct Connection {
    DESCRIPTOR_DATA *d;
    int peer;

    explicit Connection(ACCOUNT_TYPE *account) {
        int sockets[2];
        assert(socketpair(AF_UNIX, SOCK_STREAM, 0, sockets) == 0);
        d = new_descriptor();
        d->descriptor = sockets[0];
        peer = sockets[1];
        d->host = str_dup("192.0.2.1");
        d->account = account;
        d->connected = CON_GET_ACCOUNT_PASSWORD;
        ++num_descriptors;
        assert(d->account_password_attempts == 0);
    }

    ~Connection() {
        if (IS_VALID(d)) {
            close(d->descriptor);
            free_descriptor(d);
            --num_descriptors;
        }
        close(peer);
    }

    std::string output() const { return std::string(d->outbuf, d->outtop); }
    void clear() { d->outtop = d->out_prepared = 0; d->outbuf[0] = '\0'; }
};

static void new_account_flow(ACCOUNT_TYPE *account) {
    Connection connection(account);
    auto *d = connection.d;
    state_confirm_new_account_name(d, (char *)"yes", account);
    assert(d->connected == CON_GET_NEW_ACCOUNT_PASSWORD);
    assert(connection.output().find(echo_off) != std::string::npos);
    connection.clear();
    state_get_new_account_password(d, (char *)"tiny", account);
    assert(d->connected == CON_GET_NEW_ACCOUNT_PASSWORD);
    assert(connection.output().find(echo_on) == std::string::npos);
    connection.clear();
    state_get_new_account_password(d, password, account);
    assert(d->connected == CON_CONFIRM_NEW_ACCOUNT_PASSWORD);
    assert(strcmp(account->pwd, password) != 0);
    assert(connection.output().find(echo_on) == std::string::npos);
    connection.clear();
    state_confirm_new_account_password(d, wrong, account);
    assert(d->connected == CON_GET_NEW_ACCOUNT_PASSWORD);
    assert(connection.output().find("Passwords don't match") != std::string::npos);
    assert(connection.output().find(echo_on) == std::string::npos);
    state_get_new_account_password(d, password, account);
    connection.clear();
    state_confirm_new_account_password(d, password, account);
    assert(d->connected == CON_CHOOSE_CHARACTER);
    auto output = connection.output();
    assert(output.find(echo_on) != std::string::npos);
    assert(output.find(echo_on) < output.find("Account created"));
    assert(output.find("Account created") != std::string::npos);
    std::ifstream saved("../accounts/Loginregression");
    assert(saved.good());
    std::string contents(std::istreambuf_iterator<char>(saved), {});
    assert(contents.find(std::string("Password ") + account->pwd + "~") != std::string::npos);
    assert(contents.find(password) == std::string::npos);
    puts("PASS: new account validation, confirmation retry, save and echo restoration.");
}

static void existing_account_flow(ACCOUNT_TYPE *account) {
    {
        Connection first(account), second(account);
        for (int attempt = 1; attempt <= MAX_PASSWORD_ATTEMPTS; ++attempt) {
            first.clear();
            state_get_old_account_password(first.d, wrong, account);
            assert(first.d->account_password_attempts == attempt);
            assert(second.d->account_password_attempts == 0);
            if (attempt < MAX_PASSWORD_ATTEMPTS) {
                assert(IS_VALID(first.d));
                assert(first.d->connected == CON_GET_ACCOUNT_PASSWORD);
                assert(first.output().find(echo_off) != std::string::npos);
                assert(first.output().find(echo_on) == std::string::npos);
                assert(first.output().find("Characters:") == std::string::npos);
            }
        }
        assert(!IS_VALID(first.d) && first.d->connected == CON_QUITTING);
        std::string received;
        char buffer[4096];
        ssize_t bytes;
        while ((bytes = recv(first.peer, buffer, sizeof(buffer), 0)) > 0)
            received.append(buffer, bytes);
        assert(bytes == 0); // The third failure really closed the socket.
        assert(received.find("Disconnecting.") != std::string::npos);
        assert(received.find(echo_on) == std::string::npos);
        state_get_old_account_password(second.d, password, account);
        assert(second.d->connected == CON_CHOOSE_CHARACTER);
    }
    // These descriptors come from the recycler, including the exhausted connection.
    Connection first_reused(account), second_reused(account);
    for (auto *current : {&first_reused, &second_reused}) {
        auto &connection = *current;
        for (char *candidate : {(char *)"overridepassword", (char *)"OVERRIDEPASSWORD"}) {
            state_get_old_account_password(connection.d, candidate, account);
            assert(IS_VALID(connection.d));
            assert(connection.d->connected == CON_GET_ACCOUNT_PASSWORD);
            assert(connection.output().find(echo_on) == std::string::npos);
        }
        connection.clear();
        state_get_old_account_password(connection.d, password, account);
        assert(connection.d->connected == CON_CHOOSE_CHARACTER);
        assert(connection.d->account_password_attempts == 0);
        auto output = connection.output();
        assert(output.find(echo_on) != std::string::npos);
        assert(output.find(echo_on) < output.find("Characters:"));
        assert(output.find("Characters:") != std::string::npos);
    }
    puts("PASS: per-connection retry limit, actual disconnect, recycled counters and valid login.");
}

static void invalid_hashes(ACCOUNT_TYPE *account) {
    char *saved = account->pwd;
    const char *hashes[] = {nullptr, "", "x", "*", "$invalid$hash"};
    for (const char *hash : hashes) {
        Connection connection(account);
        account->pwd = const_cast<char *>(hash);
        state_get_old_account_password(connection.d, password, account);
        assert(connection.d->connected == CON_GET_ACCOUNT_PASSWORD);
        assert(connection.d->account_password_attempts == 1);
        assert(connection.output().find(echo_on) == std::string::npos);
    }
    account->pwd = saved;
    puts("PASS: missing, short and invalid account hashes fail authentication.");
}

static void character_login(ACCOUNT_TYPE *account) {
    Connection connection(account);
    CHAR_DATA ch = {};
    PC_DATA pc = {};
    ch.pcdata = &pc;
    ch.name = (char *)"Characterregression";
    ch.level = 1;
    ch.desc = connection.d;
    connection.d->character = &ch;
    connection.d->connected = CON_GET_OLD_PASSWORD;
    SET_FLAG(ch.act, PLR_SPYSHIELD);
    pc.pwd = account->pwd;
    for (char *candidate : {(char *)"overridepassword", (char *)"OVERRIDEPASSWORD"}) {
        state_get_old_password(connection.d, candidate, &ch);
        assert(connection.d->connected == CON_GET_OLD_PASSWORD);
        assert(connection.output().find(echo_on) == std::string::npos);
    }
    assert(pc.passatt == 2);
    connection.clear();
    state_get_old_password(connection.d, password, &ch);
    assert(pc.passatt == 0);
    assert(connection.d->connected == CON_READ_MOTD);
    assert(connection.output().find(echo_on) != std::string::npos);
    connection.d->character = nullptr;
    puts("PASS: account and character password overrides rejected; real passwords still accepted.");
}

int main() {
    char pool[] = "pool";
    string_space = pool;
    top_string = pool + sizeof(pool);
    current_time = 1700000000;
    troll_ip = str_dup("");
    ACCOUNT_TYPE *account = new_account();
    account->name = str_dup("Loginregression");
    new_account_flow(account);
    existing_account_flow(account);
    invalid_hashes(account);
    character_login(account);
    free_account(account);
    assert(num_descriptors == 0);
}
