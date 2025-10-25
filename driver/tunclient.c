//
// Created by akp on 25/10/2025.
//
#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <linux/if.h>
#include <linux/if_tun.h>
#include <string.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <sys/poll.h>
#include <sys/stat.h>

int tun_alloc(char *dev, int flags) {
    struct ifreq ifr;
    int fd, err;
    char *clonedev = "/dev/net/tun";

    /* Arguments taken by the function:
     *
     * char *dev: the name of an interface (or '\0'). MUST have enough
     *   space to hold the interface name if '\0' is passed
     * int flags: interface flags (eg, IFF_TUN etc.)
     */

    /* open the clone device */
    if( (fd = open(clonedev, O_RDWR)) < 0 ) {
        return fd;
    }

    /* preparation of the struct ifr, of type "struct ifreq" */
    memset(&ifr, 0, sizeof(ifr));

    ifr.ifr_flags = flags;   /* IFF_TUN or IFF_TAP, plus maybe IFF_NO_PI */

    if (*dev) {
        /* if a device name was specified, put it in the structure; otherwise,
         * the kernel will try to allocate the "next" device of the
         * specified type */
        strncpy(ifr.ifr_name, dev, IFNAMSIZ);
    }

    /* try to create the device */
    if( (err = ioctl(fd, TUNSETIFF, (void *) &ifr)) < 0 ) {
        close(fd);
        return err;
    }

    /* if the operation was successful, write back the name of the
     * interface to the variable "dev", so the caller can know
     * it. Note that the caller MUST reserve space in *dev (see calling
     * code below) */
    strcpy(dev, ifr.ifr_name);

    /* this is the special file descriptor that the caller will use to talk
     * with the virtual interface */
    return fd;
}

int write_all(int fd, const char *buf, int nbytes) {
    int n_bytes_written = 0;
    int res;

    while (n_bytes_written < nbytes) {
        printf("write: %d bytes, %d written\n", nbytes - n_bytes_written, n_bytes_written);
        res = write(fd, &buf[n_bytes_written], nbytes - n_bytes_written);
        if (res < 1) {
            return res;
        }
        n_bytes_written += res;
    }

    return n_bytes_written;
}

#define TUN_MTU 1500

int tun_readloop(int tun_fd, int downstream_fd) {
    int n_bytes_read, n_bytes_written;
    char buf[TUN_MTU];
    struct pollfd poll_fds[2];

#define IDX_TUN 0
#define IDX_DOWNSTREAM 1

    poll_fds[IDX_TUN].fd = tun_fd;
    poll_fds[IDX_TUN].events = POLLIN | POLLERR | POLLHUP;

    poll_fds[IDX_DOWNSTREAM].fd = downstream_fd;
    poll_fds[IDX_DOWNSTREAM].events = POLLIN | POLLERR | POLLHUP;

    // TODO: implement handling for POLLERR and POLLHUP
    int ready;
    while (1) {
        ready = poll(poll_fds, 2, -1);
        if (ready < 0) {
            perror("poll()");
            return ready;
        }

        if (poll_fds[IDX_TUN].revents & POLLIN) {
            n_bytes_read = read(poll_fds[IDX_TUN].fd, buf, sizeof(buf));
            if (n_bytes_read < 0) {
                perror("read from tun");
                return n_bytes_read;
            }
            printf("tun: read %d bytes\n", n_bytes_read);

            if (n_bytes_read > 0) {
                if ((n_bytes_written = write(poll_fds[IDX_DOWNSTREAM].fd, buf, n_bytes_read)) < 0) {
                    perror("write to downstream");
                    return n_bytes_written;
                }
//            if ((err = write_all(poll_fds[IDX_DOWNSTREAM].fd, buf, n_bytes_read)) < 0) {
//                perror("write to downstream");
//                return err;
//            }
                printf("downstream: wrote %d bytes\n", n_bytes_written);
            }
        }

        if (poll_fds[IDX_DOWNSTREAM].revents & POLLIN) {
            n_bytes_read = read(poll_fds[IDX_DOWNSTREAM].fd, buf, sizeof(buf));
            if (n_bytes_read < 0) {
                perror("read from downstream");
                return n_bytes_read;
            }
            printf("downstream: read %d bytes\n", n_bytes_read);

            if (n_bytes_read > 0) {
                if ((n_bytes_written = write(poll_fds[IDX_TUN].fd, buf, n_bytes_read)) < 0) {
                    perror("write to tun");
                    return n_bytes_written;
                }
                printf("tun: wrote %d bytes\n", n_bytes_written);
            }
        }
    }
    return 0;
}

int open_fifo(const char *name, int oflag, mode_t mode) {
    int err;
    if ((err = mkfifo(name, mode)) < 0 && errno != EEXIST) {
        return err;
    }
    return open(name, oflag);
}

#define TUN_IF_NAME "tun13"
#define OUTPUT_FILE_NAME "./tun-sink.fifo"

int main(int argc, char** argv) {
    int err;
    char if_name[IFNAMSIZ] = TUN_IF_NAME;

    // open IDX_TUN interface
    int tun_fd = tun_alloc(if_name, IFF_TUN | IFF_NO_PI);
    if (tun_fd < 0) {
        perror("tun_alloc()");
        return 1;
    }

    printf("if_name=%s\n", if_name);

    // open output file
    int output_fd = open_fifo(OUTPUT_FILE_NAME, O_RDWR, 0777);
    if (output_fd < 0) {
        perror("open output file");
        return 1;
    }
    printf("opened output %s\n", OUTPUT_FILE_NAME);

    printf("entering readloop\n");

    if ((err = tun_readloop(tun_fd, output_fd)) < 0) {
        perror("tun_readloop()");
        return err;
    }

    return 0;
}
