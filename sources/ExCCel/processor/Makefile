CC     := gcc
CFLAGS := -Wall -Wextra -pedantic -O0 -fno-stack-protector -no-pie -gdwarf-4 -gstrict-dwarf
LDFLAGS := -Wl,-z,relro,-z,now,--image-base=0x400000

TARGET := processor
SRCDIR := src
OUTDIR := build
SRCS := $(wildcard $(SRCDIR)/*.c)
OBJS := $(patsubst $(SRCDIR)/%.c,$(OUTDIR)/%.o,$(SRCS))
BINARY := $(OUTDIR)/$(TARGET)

.PHONY: all clean dist

all: $(BINARY)

$(OUTDIR):
	echo 'MKDIR $@'
	mkdir -p $@

$(OUTDIR)/%.o: $(SRCDIR)/%.c | $(OUTDIR)
	echo 'CC $@'
	$(CC) $(CFLAGS) -c -o $@ $<

$(BINARY): $(OBJS) | $(OUTDIR)
	echo 'CCLD $@'
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^
	cp $(BINARY) ../../../exploit/ExCCel/

clean:
	echo 'CLEAN $(OUTDIR)'
	rm -rf $(OUTDIR)
