//
// Created by akp on 25/10/2025.
// Exists to make sure that it was possible to make a FIFO pipe-style file
//
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <errno.h>

static const char* fifo_file_name = "./pipetest_file.txt";

int main(int argc, char** argv) {
    int err;

    err = mkfifo(fifo_file_name, 0777);
    if (err < 0 && errno != EEXIST) {
        perror("mkfifo()");
        return 1;
    }

    int fd = open(fifo_file_name, O_RDONLY);
    if (fd < 0) {
        perror("open()");
        return 1;
    }

    char buf[32];

    int n_bytes_read = read(fd, buf, 32);

    printf("%d bytes read\n", n_bytes_read);
    printf("data:");

    for (int i = 0; i < n_bytes_read; i += 1) {
        printf("%02X ", buf[i]);
    }

    printf("\n");
    close(fd);
    return 0;
}