.DEFAULT_GOAL := all
CC      = g++
BUILD ?= release
ifeq ($(BUILD),release)
PROF ?= -O2 -g
else ifeq ($(BUILD),debug)
PROF ?= -O0 -g3
else
$(error BUILD must be release or debug)
endif
NOCRYPT =
C_FLAGS =  -Wall -Wno-deprecated -Wno-write-strings -fno-stack-protector $(PROF) $(NOCRYPT) -I$(CURDIR)/rapidjson
L_FLAGS =  $(PROF) -Wl,--no-as-needed -ldl -rdynamic -fno-stack-protector
LIBS    = -lcrypt -lcurl
SANITIZE ?= 0
ifeq ($(SANITIZE),1)
SAN_FLAGS = -fsanitize=address,undefined -fno-omit-frame-pointer -O1 -g3
C_FLAGS += $(SAN_FLAGS)
L_FLAGS += -fsanitize=address,undefined
endif

O_FILES = abominations.o act_comm.o act_info.o act_move.o act_obj.o act_wiz.o \
	  alias.o attract.o ban.o bit.o bitarray.o \
	  Buffer.o clans.o comm.o creation.o db.o db2.o events.o\
	  flags.o fight.o ghosts.o handler.o \
	  hedit.o houses.o institute.o interp.o lookup.o  map.o mem.o\
	  music.o note_new.o olc.o olc_act.o olc_mpcode.o olc_save.o \
	  patrols.o syndicate.o dissent.o public_combat.o full_moon.o recycle.o save.o sex.o  skills.o\
	  social-edit.o social.o stories.o shifters.o string.o sys.o system.o tables.o travel.o\
	  update.o world.o room_descriptions.o recovery.o guest_progression.o feeding.o sins.o\
	  Note.o MudIo.o Util.o performance.o ai_protocol.o runtime_io.o runtime_indexes.o process_actions.o game_update.o\

# Never reuse the legacy object files committed under .build/ or src/.
# Their checkout timestamps do not establish which source produced them.
BUILD_DIR = .build-local/$(BUILD)-sanitize$(SANITIZE)
OBJECTS = $(addprefix $(BUILD_DIR)/,$(O_FILES))
DEPS = $(OBJECTS:.o=.d)

.PHONY: all clean release debug sanitize FORCE
all: haven
release:
	$(MAKE) BUILD=release SANITIZE=0 haven
debug:
	$(MAKE) BUILD=debug SANITIZE=0 haven
sanitize:
	$(MAKE) BUILD=debug SANITIZE=1 haven

# Re-check flags without changing the stamp when the configuration is unchanged.
$(BUILD_DIR)/flags: FORCE
	@mkdir -p $(BUILD_DIR)
	@printf '%s\n' '$(CC) $(C_FLAGS) $(L_FLAGS) $(LIBS)' > $@.tmp
	@cmp -s $@.tmp $@ || cp $@.tmp $@
	@rm -f $@.tmp

# Link once per configuration. Install a hard link with rename to preserve
# running inodes; file identity makes no-op builds independent of binary size.
$(BUILD_DIR)/haven: $(OBJECTS) $(BUILD_DIR)/flags Makefile
	$(CC) $(L_FLAGS) -o $@.tmp $(OBJECTS) $(LIBS)
	mv -f $@.tmp $@

haven: $(BUILD_DIR)/haven FORCE
	@test $(BUILD_DIR)/haven -ef haven || { ln -f $(BUILD_DIR)/haven haven.tmp && mv -f haven.tmp haven; }
resolve: 
	rm -f resolve
	$(CC) $(L_FLAGS) -o resolve resolve.c $(LIBS)
web:
	rm -f webserver
	rm -f webclient
	$(CC) $(L_FLAGS) -o webserver webserver.c $(LIBS)
	$(CC) $(L_FLAGS) -o webclient webclient.c $(LIBS)

$(BUILD_DIR)/%.o: %.c $(BUILD_DIR)/flags
	$(CC) -MMD -MP -c $(C_FLAGS) $< -o $@
$(BUILD_DIR)/%.o: %.cc $(BUILD_DIR)/flags
	$(CC) -MMD -MP -c $(C_FLAGS) $< -o $@

-include $(DEPS)

clean:
	rm -rf .build .build-local
	rm -f *.o haven haven.tmp
