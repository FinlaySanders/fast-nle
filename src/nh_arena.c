#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <sys/mman.h>
#include "hack.h"
#include "nle.h"
#include "nh_arena.h"
#undef free
#undef settings

#define NH_ARENA_RESERVE ((size_t) 64 << 20)
#define NH_ARENA_MAXCLS 64 /* 16..1024 byte payloads */

struct nh_arena {
    char *base;
    size_t cap, used;
    void *fl[NH_ARENA_MAXCLS + 1];
};
typedef struct { uint32_t cls; uint32_t magic; uint64_t pad; } nh_hdr; /* 16 bytes */

nh_arena *
nh_arena_new(void)
{
    nh_arena *a = (nh_arena *) calloc(1, sizeof *a);
    if (!a)
        return NULL;
    a->base = (char *) mmap(NULL, NH_ARENA_RESERVE, PROT_READ | PROT_WRITE,
                            MAP_PRIVATE | MAP_ANONYMOUS | MAP_NORESERVE, -1, 0);
    if (a->base == MAP_FAILED) {
        (free)(a);
        return NULL;
    }
    a->cap = NH_ARENA_RESERVE;
    return a;
}

void
nh_arena_destroy(nh_arena *a)
{
    if (!a)
        return;
    munmap(a->base, a->cap);
    (free)(a);
}

static inline int
nh_arena_owns(const nh_arena *a, const void *p)
{
    return (const char *) p >= a->base && (const char *) p < a->base + a->cap;
}

static void *
nh_arena_alloc(nh_arena *a, size_t lth)
{
    size_t cls = (lth + 15) >> 4;
    nh_hdr *h;
    if (cls == 0)
        cls = 1;
    if (cls > NH_ARENA_MAXCLS)
        return NULL; /* big blocks stay on libc */
    if (a->fl[cls]) {
        void *p = a->fl[cls];
        a->fl[cls] = *(void **) p;
        memset(p, 0, cls << 4);
        return p;
    }
    {
        size_t need = 16 + (cls << 4);
        if (a->used + need > a->cap)
            return NULL; /* reservation exhausted: libc from here on */
        h = (nh_hdr *) (a->base + a->used);
        a->used += need;
        h->cls = (uint32_t) cls;
        h->magic = 0xA11Cu;
        return h + 1; /* fresh pages are zero */
    }
}

static void
nh_arena_dealloc(nh_arena *a, void *p)
{
    nh_hdr *h = (nh_hdr *) p - 1;
    *(void **) p = a->fl[h->cls];
    a->fl[h->cls] = p;
}

void *
nh_arena_alloc_hook(unsigned int lth)
{
    nle_ctx_t *c = current_nle_ctx;
    return (c && c->arena) ? nh_arena_alloc((nh_arena *) c->arena, lth) : NULL;
}

void
nh_arena_free_hook(void *p)
{
    nle_ctx_t *c = current_nle_ctx;
    if (p && c && c->arena && nh_arena_owns((nh_arena *) c->arena, p))
        nh_arena_dealloc((nh_arena *) c->arena, p);
    else
        (free)(p);
}
