CC := clang
CFLAGS := -g
CPPFLAGS := -Wall

BUILD_DIR := ./build
DIRS := ${shell find . -type d -print}

#.PHONY: $(DIRS)

$(BUILD_DIR)/$(DIRS).o: %.c
	mkdir -p $(dir $(BUILD_DIR))
	$(CC) $(CFLAGS) -c $< -o $@


