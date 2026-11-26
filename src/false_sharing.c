/*
 * Uso: false_sharing HILOS {nopad|pad} [INCREMENTOS_POR_HILO]
 * Nativo: cc -std=c11 -O2 -Wall -Wextra -Wpedantic -pthread false_sharing.c -o false_sharing
 * Para gem5, compilar con -DGEM5_ROI, las cabeceras de gem5 y libm5.a
 * para la ISA del simulador. La ROI abarca la liberación y unión de los
 * hilos. La creación, inicialización y verificación quedan fuera.
 */
#include <errno.h>
#include <inttypes.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef GEM5_ROI
#include <gem5/m5ops.h>
#endif

enum { CACHE_LINE = 64, MAX_THREADS = 8 };
static const uint64_t default_iterations = UINT64_C(100000);

typedef struct {
    _Alignas(CACHE_LINE) volatile uint64_t value;
} PaddedCounter;

static _Alignas(CACHE_LINE) volatile uint64_t packed[MAX_THREADS];
static PaddedCounter padded[MAX_THREADS];

_Static_assert(sizeof(packed) == CACHE_LINE,
               "Packed counters must fit in one cache line");
_Static_assert(_Alignof(PaddedCounter) == CACHE_LINE &&
               sizeof(PaddedCounter) == CACHE_LINE,
               "Padded counters must be aligned and spaced by one cache line");

typedef struct {
    volatile uint64_t *counter;
    uint64_t iterations;
} Worker;

static pthread_mutex_t start_mutex = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t start_cond = PTHREAD_COND_INITIALIZER;
static bool start;
static bool cancelled;

static bool parse_positive(const char *text, uint64_t *value)
{
    if (*text == '\0' || text[strspn(text, "0123456789")] != '\0') {
        return false;
    }

    errno = 0;
    uintmax_t number = strtoumax(text, NULL, 10);
    if (errno == ERANGE || number == 0 || number > UINT64_MAX) {
        return false;
    }

    *value = (uint64_t)number;
    return true;
}

static void increment(const Worker *worker)
{
    /* Un único escritor por contador. Volatile conserva cada lectura y escritura. */
    for (uint64_t i = 0; i < worker->iterations; ++i) {
        ++*worker->counter;
    }
}

static void *run_worker(void *arg)
{
    pthread_mutex_lock(&start_mutex);
    while (!start) {
        pthread_cond_wait(&start_cond, &start_mutex);
    }
    bool run = !cancelled;
    pthread_mutex_unlock(&start_mutex);

    if (run) {
        increment(arg);
    }
    return NULL;
}

int main(int argc, char **argv)
{
    uint64_t count;
    uint64_t iterations = default_iterations;
    if (argc < 3 || argc > 4 ||
        !parse_positive(argv[1], &count) || count > MAX_THREADS ||
        (strcmp(argv[2], "nopad") != 0 && strcmp(argv[2], "pad") != 0) ||
        (argc == 4 && !parse_positive(argv[3], &iterations))) {
        fprintf(stderr, "Uso: %s HILOS(1-8) {nopad|pad} [INCREMENTOS_POR_HILO]\n",
                argv[0]);
        return EXIT_FAILURE;
    }

    size_t threads = (size_t)count;
    bool with_padding = strcmp(argv[2], "pad") == 0;
    Worker workers[MAX_THREADS];
    pthread_t children[MAX_THREADS - 1];

    for (size_t i = 0; i < threads; ++i) {
        workers[i].counter = with_padding ? &padded[i].value : &packed[i];
        workers[i].iterations = iterations;
        *workers[i].counter = 0;
    }

    /* El hilo principal cuenta como un trabajador. */
    size_t next = 1;
    for (; next < threads; ++next) {
        int err = pthread_create(&children[next - 1], NULL, run_worker,
                                 &workers[next]);
        if (err != 0) {
            fprintf(stderr, "pthread_create: %s\n", strerror(err));
            break;
        }
    }

    pthread_mutex_lock(&start_mutex);
    cancelled = next != threads;
#ifdef GEM5_ROI
    if (!cancelled) {
        m5_reset_stats(0, 0);
    }
#endif
    start = true;
    pthread_cond_broadcast(&start_cond);
    pthread_mutex_unlock(&start_mutex);

    if (!cancelled) {
        increment(&workers[0]);
    }
    for (size_t i = 1; i < next; ++i) {
        int err = pthread_join(children[i - 1], NULL);
        if (err != 0) {
            fprintf(stderr, "pthread_join: %s\n", strerror(err));
            return EXIT_FAILURE;
        }
    }
    if (cancelled) {
        return EXIT_FAILURE;
    }
#ifdef GEM5_ROI
    m5_dump_stats(0, 0);
#endif

    bool verified = true;
    printf("%s hilos=%zu esperado=%" PRIu64 "\n", argv[2], threads, iterations);
    for (size_t i = 0; i < threads; ++i) {
        uint64_t actual = *workers[i].counter;
        printf("contador[%zu]=%" PRIu64 "\n", i, actual);
        verified = verified && actual == iterations;
    }
    puts(verified ? "Verificación: OK" : "Verificación: ERROR");
    return verified ? EXIT_SUCCESS : EXIT_FAILURE;
}
