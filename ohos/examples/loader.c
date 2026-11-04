#include <dlfcn.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>

static char *(*hello_fn)(void);
static void (*free_fn)(char *);

static void *worker(void *unused) {
    (void)unused;
    for (int i = 0; i < 100; ++i) {
        char *value = hello_fn();
        if (!value || !strstr(value, "openharmony=true")) {
            if (value) free_fn(value);
            return (void *)1;
        }
        free_fn(value);
    }
    return NULL;
}

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: loader /absolute/path/libohos_example.so\n"); return 2; }
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) { fprintf(stderr, "dlopen failed\n"); return 3; }
    hello_fn = (char *(*)(void))dlsym(handle, "OhosHello");
    free_fn = (void (*)(char *))dlsym(handle, "OhosFree");
    if (!hello_fn || !free_fn) return 4;
    pthread_t threads[4];
    int created = 0, result = 0;
    for (; created < 4; ++created) {
        if (pthread_create(&threads[created], NULL, worker, NULL)) { result = 5; break; }
    }
    for (int i = 0; i < created; ++i) {
        void *status = NULL;
        if (pthread_join(threads[i], &status) || status) result = 6;
    }
    if (!result) puts("PASS: 400 callbacks on four pthreads");
    /* Do not dlclose a live Go runtime. Process exit owns final teardown. */
    return result;
}
