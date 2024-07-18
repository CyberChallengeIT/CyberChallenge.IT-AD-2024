SRCDIR     := cgi
OUTDIR     := www/cgi-bin

LIB_SRCDIR := $(SRCDIR)/lib
LIB_SRCS   := $(wildcard $(LIB_SRCDIR)/*.cc)
LIB_OBJS   := $(LIB_SRCS:.cc=.o)
LIB_DEPS   := $(LIB_OBJS:.o=.d)

CGI_SRCS := $(wildcard $(SRCDIR)/*.cc)
CGI_OBJS := $(filter-out $(LIB_OBJS),$(CGI_SRCS:.cc=.o))
CGI_DEPS := $(CGI_OBJS:.o=.d)
CGI_BINS := $(CGI_OBJS:$(SRCDIR)/%.o=$(OUTDIR)/%.cgi)

CXXFLAGS := -std=c++17 -Wall -Wextra -MMD -ffunction-sections
LDFLAGS  := -lcrypt -lcgicc -lsqlite3

-include $(LIB_DEPS) $(CGI_DEPS)

.DEFAULT_GOAL := all
.PHONY: all clean

all: $(CGI_BINS)

$(SRCDIR)/%.o: $(SRCDIR)/%.cc
	$(CXX) $(CXXFLAGS) -c -o $@ $<

$(OUTDIR)/%.cgi: $(SRCDIR)/%.o $(LIB_OBJS)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -fr $(CGI_BINS) $(CGI_OBJS) $(CGI_DEPS) $(LIB_OBJS) $(LIB_DEPS)
