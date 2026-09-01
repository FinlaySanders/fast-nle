/* fcontext backend for wasm: emscripten (Asyncify) fibers behind deboost's
 * 5-symbol API. Native builds keep deboost's assembly; wasm forbids stack
 * switching, so each fcontext becomes an emscripten fiber. The emfc struct
 * and asyncify stack are carved from the top of the create_fcontext_stack
 * allocation so the deboost lifecycle (create/make/jump/destroy) needs no
 * extra bookkeeping. Requires -sASYNCIFY at link. */
#ifdef __EMSCRIPTEN__
#include <emscripten/fiber.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcontext/fcontext.h>

#define EMFC_ASYNC_SZ (1 << 18)

typedef struct emfc {
    emscripten_fiber_t fib;
    struct emfc *from;
    void *data;
    pfn_fcontext fn;
} emfc_t;

static emfc_t emfc_main;
static char emfc_main_async[EMFC_ASYNC_SZ];
static emfc_t *emfc_cur = NULL;

static emfc_t *
emfc_self(void)
{
    if (!emfc_cur) {
        emscripten_fiber_init_from_current_context(&emfc_main.fib,
            emfc_main_async, EMFC_ASYNC_SZ);
        emfc_cur = &emfc_main;
    }
    return emfc_cur;
}

static void
emfc_entry(void *arg)
{
    emfc_t *f = (emfc_t *) arg;
    f->fn((fcontext_transfer_t){ (fcontext_t) f->from, f->data });
    abort(); /* coroutine returned without jumping out */
}

fcontext_transfer_t
jump_fcontext(fcontext_t const to, void *vp)
{
    emfc_t *self = emfc_self(), *t = (emfc_t *) to;
    t->from = self;
    t->data = vp;
    emfc_cur = t;
    emscripten_fiber_swap(&self->fib, &t->fib);
    emfc_cur = self;
    return (fcontext_transfer_t){ (fcontext_t) self->from, self->data };
}

fcontext_t
make_fcontext(void *sp, size_t size, pfn_fcontext corofn)
{
    char *top = (char *) sp;
    emfc_t *f = (emfc_t *) (((uintptr_t)(top - sizeof(emfc_t))) & ~(uintptr_t) 15);
    char *async = (char *) f - EMFC_ASYNC_SZ;
    char *base = top - size;
    memset(f, 0, sizeof(*f));
    f->fn = corofn;
    emscripten_fiber_init(&f->fib, emfc_entry, f, base, (size_t)(async - base),
                          async, EMFC_ASYNC_SZ);
    return (fcontext_t) f;
}

fcontext_stack_t
create_fcontext_stack(size_t size)
{
    /* no guard pages in wasm and one demo env: be generous, the asyncify
     * stack and emfc struct are carved from the top of this block */
    if (size < (1u << 21)) size = 1u << 21;
    fcontext_stack_t s;
    char *base = (char *) malloc(size);
    s.sptr = base ? base + size : NULL;
    s.ssize = size;
    return s;
}

void
destroy_fcontext_stack(fcontext_stack_t *s)
{
    if (s && s->sptr) free((char *) s->sptr - s->ssize);
    memset(s, 0, sizeof(*s));
}
#endif /* __EMSCRIPTEN__ */
