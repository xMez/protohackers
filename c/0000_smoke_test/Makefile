CC := clang
CFLAGS := -g -Wall -pedantic -Wsystem-headers

TARGET := smoke_test
SRCS = $(wildcard *.c)

all: $(TARGET)

$(TARGET): $(TARGET).c
	$(CC) $(CFLAGS) -o $@ $(TARGET).c

clean:
	$(RM) $(TARGET)
