// Stock-NLE engine backend for the PufferLib NetHack vec: every env gets its own
// private copy of stock libnethack.so (loaded from a memfd, so each copy has its
// own globals), stepped through stock's nle_start/nle_step/nle_end. The fork-only
// introspection hooks the env reads are derived from stock's public observation
// by nh_derive.h. The configuration is the NetHack Challenge interface: NLE's option
// string, no screen descriptions, every key is a step, 1e6 steps / 10,000 clock-less steps end the episode.
#define _GNU_SOURCE
#include <ctype.h>
#include <dlfcn.h>
#include <elf.h>
#include <time.h>
#include <link.h>
#include <ucontext.h>
#include <errno.h>
#include <fcntl.h>
#include <setjmp.h>
#include <signal.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include "nletypes.h" // the fork's nle_obs / nle_settings: what the env compiles against
#include "nh_derive.h"

#define ROWS 21
#define COLS 79
#define TTY_LI 24
#define TTY_CO 80
#define SDESC 80
#define INV 55
#define STOCK_INTERNAL 9
#define STOCK_PROG 6
#define NH_STOCK_DEFAULT_OPTIONS "autopickup,color,disclose:+i +a +v +g +c +o,mention_walls,nobones,nocmdassist,nolegacy,nosparkle,pickup_burden:unencumbered,pickup_types:$?!/,runmode:teleport,showexp,showscore,time,name:Agent-@,race:random,gender:random,align:random"

// stock NLE 0.9.0 ABI (verified with offsetof: obs 152 B, settings 49156 B, seeds 24 B)
typedef struct {
    int action;
    int done;
    char in_normal_game;
    int how_done;
    short* glyphs;
    unsigned char* chars;
    unsigned char* colors;
    unsigned char* specials;
    long* blstats;
    unsigned char* message;
    int* program_state;
    int* internal;
    short* inv_glyphs;
    unsigned char* inv_strs;
    unsigned char* inv_letters;
    unsigned char* inv_oclasses;
    unsigned char* screen_descriptions;
    unsigned char* tty_chars;
    signed char* tty_colors;
    unsigned char* tty_cursor;
    int* misc;
} sobs_t;
typedef struct {
    char hackdir[4096];
    char scoreprefix[4096];
    char options[32768];
    char wizkit[4096];
    int spawn_monsters;
    char ttyrecname[4096];
} sset_t;
typedef struct {
    unsigned long seeds[2];
    char reseed;
} sseed_t;

typedef struct Inst {
    void* dl;
    int fd;
    void* ctx; // stock's nle_ctx_t
    void* (*s_start)(sobs_t*, FILE*, sseed_t*, sset_t*);
    void* (*s_step)(void*, sobs_t*);
    void (*s_end)(void*);
    sobs_t so;
    nle_obs* fobs; // the env's observation (fork layout)
    DObs d;        // the derivation module's view of the same buffers
    DState S;
    // buffers for channels the env does not bind, or binds at a different size
    short glyphs[ROWS * COLS];
    unsigned char chars[ROWS * COLS];
    unsigned char colors[ROWS * COLS];
    unsigned char specials[ROWS * COLS];
    long blstats[NLE_BLSTATS_SIZE];
    unsigned char message[NLE_MESSAGE_SIZE];
    int prog[STOCK_PROG];
    int internal[STOCK_INTERNAL];
    short inv_glyphs[INV];
    unsigned char inv_strs[INV * NLE_INVENTORY_STR_LENGTH];
    unsigned char inv_letters[INV];
    unsigned char inv_oclasses[INV];
    unsigned char sdesc[ROWS * COLS * SDESC];
    unsigned char tty_chars[TTY_LI * TTY_CO];
    signed char tty_colors[TTY_LI * TTY_CO];
    unsigned char tty_cursor[2];
    int misc[NLE_MISC_SIZE];
    sset_t sset;
    int mapped; // glyph buffers currently hold exported (mapped) glyphs
    unsigned long seed0;
    int crashed; // the engine faulted inside this instance: its coroutine is abandoned, never resumed or torn down
    int vmore; char vmore_text[256]; // virtual --More--: the fork's getpos shortcut leaves the pre-prompt message unacknowledged, so the redraw that follows shows --More-- and eats keys until space/Enter/ESC; stock's real getpos (answered here) clears the line instead // raw terminal stream since the last reset (tmt_write interposed): the derive reads pile windows from it
    char topl_save[256]; int topl_saved; long probe_mark; // the top-line message as the key left it, put back after the probes
    long ch_steps, ch_noprog, ch_maxnoprog, ch_turn; int ch_aborted; // NetHackChallenge step accounting
    long last_bl[27]; int ep_logged; // blstats before the latest key (the done observation is zeroed); per-episode log written
} Inst;


// ---------------------------------------------------------------- library image
static unsigned char* g_img;
static size_t g_img_len;
static const char* stock_lib_path(void) {
    const char* p = getenv("NLE_STOCK_LIB");
    if (!p || !*p) { fprintf(stderr, "nh_stock: set NLE_STOCK_LIB to stock NLE's libnethack.so (and NETHACKDIR to its nethackdir)\n"); exit(2); }
    return p;
}
static void load_image(void) {
    if (g_img) return;
    static int lock;
    while (__sync_lock_test_and_set(&lock, 1)) {}
    if (!g_img) {
        int fd = open(stock_lib_path(), O_RDONLY);
        if (fd < 0) { fprintf(stderr, "nh_stock: cannot open %s: %s\n", stock_lib_path(), strerror(errno)); exit(1); }
        struct stat st; fstat(fd, &st);
        unsigned char* buf = (unsigned char*)malloc((size_t)st.st_size);
        size_t got = 0;
        while (got < (size_t)st.st_size) {
            ssize_t r = read(fd, buf + got, (size_t)st.st_size - got);
            if (r <= 0) { fprintf(stderr, "nh_stock: short read of %s\n", stock_lib_path()); exit(1); }
            got += (size_t)r;
        }
        close(fd);
        g_img_len = got;
        __sync_synchronize();
        g_img = buf;
    }
    __sync_lock_release(&lock);
}

static int inst_open_lib(Inst* in) {
    load_image();
    in->fd = memfd_create("libnethack_stock", MFD_CLOEXEC);
    if (in->fd < 0) { fprintf(stderr, "nh_stock: memfd_create: %s\n", strerror(errno)); return -1; }
    size_t off = 0;
    while (off < g_img_len) {
        ssize_t w = write(in->fd, g_img + off, g_img_len - off);
        if (w <= 0) { fprintf(stderr, "nh_stock: memfd write: %s\n", strerror(errno)); return -1; }
        off += (size_t)w;
    }
    char path[64];
    snprintf(path, sizeof path, "/proc/self/fd/%d", in->fd);
    in->dl = dlopen(path, RTLD_NOW | RTLD_LOCAL);
    if (!in->dl) { fprintf(stderr, "nh_stock: dlopen: %s\n", dlerror()); return -1; }
    in->s_start = (void* (*)(sobs_t*, FILE*, sseed_t*, sset_t*))dlsym(in->dl, "nle_start");
    in->s_step = (void* (*)(void*, sobs_t*))dlsym(in->dl, "nle_step");
    in->s_end = (void (*)(void*))dlsym(in->dl, "nle_end");
    if (!in->s_start || !in->s_step || !in->s_end) { fprintf(stderr, "nh_stock: missing stock symbols\n"); return -1; }
    return 0;
}
static void inst_close_lib(Inst* in) {
    if (in->dl) { dlclose(in->dl); in->dl = NULL; }
    if (in->fd >= 0) { close(in->fd); in->fd = -1; }
}

// ---------------------------------------------------------------- engine crash isolation
// Stock NLE 0.9.0 has at least one known in-engine segfault (NLE issue #100: launch_obj rolls a boulder out of
// bounds; the fork fixed it in 0d9e5946e with an isok() check). The engine stays unmodified, so a fault inside a
// game must not take the whole eval down: every engine call runs under a per-thread sigsetjmp; the handler jumps
// back, the instance is marked crashed (episode ends, how_done -1) and its coroutine is abandoned.
static __thread Inst* t_cur;
static __thread sigjmp_buf t_jb;
static __thread volatile int t_jb_set;
static __thread char* t_altstack;
static long g_crashes;
static __thread unsigned long t_fault_pc;
static void crash_handler(int sig, siginfo_t* si, void* uc) {
    (void)si;
    t_fault_pc = uc ? (unsigned long)((ucontext_t*)uc)->uc_mcontext.gregs[REG_RIP] : 0UL;
    if (t_jb_set) { t_jb_set = 0; siglongjmp(t_jb, sig); }
    signal(sig, SIG_DFL); raise(sig);
}
static void crash_report(void) { if (g_crashes) fprintf(stderr, "nh_stock: %ld episode(s) ended by an in-engine fault (stock NLE bug; the episode counts as died)\n", g_crashes); }
static void crash_guard_init(void) {
    static int done;
    if (!done && __sync_bool_compare_and_swap(&done, 0, 1)) {
        struct sigaction sa; memset(&sa, 0, sizeof sa);
        sa.sa_sigaction = crash_handler; sa.sa_flags = SA_SIGINFO | SA_ONSTACK | SA_NODEFER; sigemptyset(&sa.sa_mask);
        sigaction(SIGSEGV, &sa, NULL); sigaction(SIGBUS, &sa, NULL); sigaction(SIGFPE, &sa, NULL); sigaction(SIGILL, &sa, NULL);
        atexit(crash_report);
    }
    if (!t_altstack) { t_altstack = (char*)malloc(1 << 16); stack_t ss; ss.ss_sp = t_altstack; ss.ss_size = 1 << 16; ss.ss_flags = 0; sigaltstack(&ss, NULL); }
}
static void crash_note(Inst* in, int sig, const char* where) {
    in->crashed = 1; in->so.done = 1; in->so.how_done = -1;
    long k = __sync_add_and_fetch(&g_crashes, 1);
    unsigned long off = 0; { struct link_map* lm = NULL; if (in->dl && dlinfo(in->dl, RTLD_DI_LINKMAP, &lm) == 0 && lm) off = t_fault_pc - (unsigned long)lm->l_addr; }
    if (k <= 20) fprintf(stderr, "nh_stock: engine fault (signal %d) in %s at lib+0x%lx, #%ld, seed %lx turn %ld depth %ld last key %d: episode ended\n", sig, where, off, k, in->seed0, in->d.blstats ? in->d.blstats[20] : -1L, in->d.blstats ? in->d.blstats[12] : -1L, in->so.action);
}
static int guarded_step(Inst* in) { // 1 = the engine faulted
    crash_guard_init(); t_cur = in;
    int sig = sigsetjmp(t_jb, 1);
    if (sig == 0) { t_jb_set = 1; in->s_step(in->ctx, &in->so); t_jb_set = 0;
        in->ch_steps++; if (in->d.blstats) { long t = in->d.blstats[20]; if (t == in->ch_turn) { if (++in->ch_noprog > in->ch_maxnoprog) in->ch_maxnoprog = in->ch_noprog; } else { in->ch_turn = t; in->ch_noprog = 0; } }
        return 0; }
    crash_note(in, sig, "nle_step"); return 1;
}
static int guarded_start(Inst* in, sseed_t* seed) { // 1 = the engine faulted during start-up
    crash_guard_init(); t_cur = in;
    int sig = sigsetjmp(t_jb, 1);
    if (sig == 0) { t_jb_set = 1; in->ctx = in->s_start(&in->so, NULL, seed, &in->sset); t_jb_set = 0; return 0; }
    crash_note(in, sig, "nle_start"); return 1;
}


// ---------------------------------------------------------------- clock
// Stock NetHack reads the wall clock (ubirthday at reset; getlt() for the moon phase, Friday 13th, night and midnight) and
// the challenge plays under the real one. NH_STOCK_FIXEDCLOCK=<unix seconds> pins every game to that instant instead: the
// copies' GOT entries for time() and localtime() are pointed at the two functions below (the engine image stays unmodified).
static long nh_fixed_clock(void) { static long v = -2; if (v == -2) { const char* e = getenv("NH_STOCK_FIXEDCLOCK"); v = e ? atol(e) : -1; } return v; }
static time_t nh_fake_time(time_t* tloc) { time_t v = (time_t)nh_fixed_clock(); if (tloc) *tloc = v; return v; }
static struct tm* nh_fake_localtime(const time_t* t) { static __thread struct tm tmv; time_t v = (time_t)nh_fixed_clock(); (void)t; gmtime_r(&v, &tmv); return &tmv; }
static int nh_patch_got(Inst* in) { // redirect the copy's imports of time/localtime when the clock is pinned; returns the slots patched
    if (nh_fixed_clock() < 0) return 0;
    struct link_map* lm = NULL; if (dlinfo(in->dl, RTLD_DI_LINKMAP, &lm) != 0 || !lm) return -1;
    ElfW(Dyn)* d = lm->l_ld; const char* strtab = NULL; ElfW(Sym)* symtab = NULL; ElfW(Rela)* jmprel = NULL; size_t jmpsz = 0; ElfW(Rela)* rela = NULL; size_t relasz = 0;
    for (; d->d_tag != DT_NULL; d++) {
        if (d->d_tag == DT_STRTAB) strtab = (const char*)d->d_un.d_ptr; else if (d->d_tag == DT_SYMTAB) symtab = (ElfW(Sym)*)d->d_un.d_ptr;
        else if (d->d_tag == DT_JMPREL) jmprel = (ElfW(Rela)*)d->d_un.d_ptr; else if (d->d_tag == DT_PLTRELSZ) jmpsz = d->d_un.d_val;
        else if (d->d_tag == DT_RELA) rela = (ElfW(Rela)*)d->d_un.d_ptr; else if (d->d_tag == DT_RELASZ) relasz = d->d_un.d_val;
    }
    if (!strtab || !symtab) return -1;
    int n = 0; long page = sysconf(_SC_PAGESIZE);
    for (int pass = 0; pass < 2; pass++) {
        ElfW(Rela)* r = pass ? rela : jmprel; size_t sz = pass ? relasz : jmpsz; if (!r) continue;
        for (size_t i = 0; i < sz / sizeof(ElfW(Rela)); i++) {
            unsigned type = ELF64_R_TYPE(r[i].r_info); if (type != R_X86_64_JUMP_SLOT && type != R_X86_64_GLOB_DAT) continue;
            const char* name = strtab + symtab[ELF64_R_SYM(r[i].r_info)].st_name; void* fn = NULL;
            if (!strcmp(name, "time")) fn = (void*)nh_fake_time; else if (!strcmp(name, "localtime")) fn = (void*)nh_fake_localtime; else continue;
            void** slot = (void**)(lm->l_addr + r[i].r_offset);
            mprotect((void*)((unsigned long)slot & ~(page - 1)), page, PROT_READ | PROT_WRITE);
            *slot = fn; n++;
        }
    }
    return n;
}

// ---------------------------------------------------------------- obs wiring
// Stock writes into the env's buffers wherever the env bound one of the same
// size; everything else lands in the instance's own buffers. Stock's internal
// has 9 slots, the fork's 11: stock writes the first 9 of the env's array.
static void wire_obs(Inst* in, nle_obs* o) {
    // sticky binding: the env passes partial obs structs on intermediate calls (some buffers NULL); a buffer is
    // replaced only by a non-NULL one, so stock keeps writing where the env last asked it to
    sobs_t* s = &in->so;
    if (!s->glyphs) { int act = s->action, done = s->done, how = s->how_done; char ing = s->in_normal_game; memset(s, 0, sizeof *s); s->action = act; s->done = done; s->how_done = how; s->in_normal_game = ing; }
#define NHB(f, mine) s->f = o->f ? o->f : (s->f ? s->f : in->mine)
    NHB(glyphs, glyphs); NHB(chars, chars); NHB(colors, colors); NHB(specials, specials); NHB(blstats, blstats); NHB(message, message);
    s->program_state = o->prog_state ? o->prog_state : (s->program_state ? s->program_state : in->prog);
    NHB(internal, internal); NHB(inv_glyphs, inv_glyphs); NHB(inv_strs, inv_strs); NHB(inv_letters, inv_letters); NHB(inv_oclasses, inv_oclasses);
    s->screen_descriptions = NULL; // never: stock builds descriptions with mksobj (RNG) and marks adjacent objects dknown
    NHB(tty_chars, tty_chars); NHB(tty_colors, tty_colors); NHB(tty_cursor, tty_cursor); NHB(misc, misc);
#undef NHB
    DObs* d = &in->d;
    d->glyphs = s->glyphs; d->blstats = s->blstats; d->message = s->message; d->misc = s->misc;
    d->tty_chars = s->tty_chars; d->tty_colors = s->tty_colors; d->tty_cursor = s->tty_cursor; d->sdesc = NULL; d->rawout = NULL; d->rawlen = NULL; // the challenge interface has no screen descriptions and no raw terminal stream
    d->inv_glyphs = s->inv_glyphs; d->inv_strs = s->inv_strs; d->inv_letters = s->inv_letters; d->inv_oclasses = s->inv_oclasses;
    if (o->internal) d->internal = o->internal; if (o->inv_state) d->inv_state = o->inv_state; if (o->inv_true_glyphs) d->inv_true = o->inv_true_glyphs;
    d->redrawn = NULL;
}

static void sync_status(Inst* in, nle_obs* o) {
    o->done = in->so.done;
    o->how_done = in->so.how_done;
    o->in_normal_game = in->so.in_normal_game;
    if (o->internal) { o->internal[9] = 0; o->internal[10] = 0; }
}

static void topl_save(Inst* in) { if (in->d.message) { memcpy(in->topl_save, in->d.message, 256); in->topl_saved = 1; in->probe_mark = in->S.probe_keys; } else in->topl_saved = 0; }
static void topl_restore(Inst* in) { if (!in->topl_saved) return; in->topl_saved = 0; if (in->S.probe_keys != in->probe_mark && in->d.message) memcpy(in->d.message, in->topl_save, 256); } // a probe ran: put the key's own message back
static void topl_restore_always(Inst* in) { if (!in->topl_saved) return; in->topl_saved = 0; if (in->d.message) memcpy(in->d.message, in->topl_save, 256); }
static int stock_send(void* ctx, int key);
// The fork's getpos() returns at once (headless port: abort when the caller allows it, else the hero's own square).
// Stock's getpos is the interactive cursor browse and raises no misc flag; it announces itself with the verbose
// "(For instructions type a '?')" line. Answer it the fork's way and put the top line back as the fork would show it.
static void nh_answer_getpos(Inst* in) {
    for (int it = 0; it < 3; it++) {
        if (in->d.misc && (in->d.misc[0] || in->d.misc[1] || in->d.misc[2])) return;
        char m[256]; dr_msg(&in->d, m, sizeof m); char* mk = strstr(m, "(For instructions type a"); if (!mk) return;
        int force = strstr(m, "Where do you want") != NULL || strstr(m, "the desired") != NULL;
        topl_save(in); stock_send(in, force ? '.' : 27);
        char post[256]; post[0] = 0; if (in->d.message) snprintf(post, sizeof post, "%.255s", (const char*)in->d.message); int post_wait = in->d.misc && (in->d.misc[0] || in->d.misc[1] || in->d.misc[2]);
        topl_restore_always(in);
        *mk = 0; { char* e = m + strlen(m); while (e > m && e[-1] == ' ') *--e = 0; }
        if (!force && m[0] && !post_wait && !in->so.done) { in->vmore = 1; snprintf(in->vmore_text, sizeof in->vmore_text, "%s", post); if (in->d.misc) in->d.misc[2] = 1; }
        if (in->d.message) { memset(in->d.message, 0, 256); snprintf((char*)in->d.message, 256, "%s", m); }
    }
}
static int stock_send(void* ctx, int key) { // zero-time probe key straight to the stock instance
    Inst* in = (Inst*)ctx;
    if (in->so.done) return 1; // a finished coroutine must never be resumed (jump into a dead context)
    in->so.action = key;
    guarded_step(in);
    return in->so.done;
}

// ---------------------------------------------------------------- engine entry points (fork signatures)
// Interposed for the stock engine copies (RTLD_LOCAL libs resolve their PLT calls against the executable first):
// stock nle.c runs the whole game on a create_fcontext_stack(64 KiB) coroutine stack, which overflows on deep call
// chains under this policy (throw/explode cascades) and corrupts the engine context -> "NetHack exit with status
// <garbage>". The fork's fix is 256 KiB. Same layout as deboost (mmap + one guard page, sptr = top, ssize = mapped
// size) so the engine's own destroy_fcontext_stack() unmaps it.
// fcontext_stack_t comes from the fork headers already included via nletypes.h (same layout as stock: sptr, ssize)
fcontext_stack_t create_fcontext_stack(size_t size) {
    static size_t want;
    if (!want) want = 256 * 1024;
    size_t page = (size_t)sysconf(_SC_PAGESIZE);
    size_t sz = size < want ? want : size;
    sz = (sz / page) * page; if (sz < 2 * page) sz = 2 * page;
    fcontext_stack_t s = {0, 0};
    void* vp = mmap(0, sz, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (vp == MAP_FAILED) return s;
    mprotect(vp, page, PROT_NONE);
    s.sptr = (char*)vp + sz; s.ssize = sz;
    { static int once; if (__sync_bool_compare_and_swap(&once, 0, 1)) fprintf(stderr, "nh_stock: coroutine stack %zu KiB (interposed; engine asked for %zu KiB)\n", sz / 1024, size / 1024); }
    return s;
}

nle_ctx_t* nle_start(nle_obs* obs, FILE* f, nle_settings* set) {
    (void)f;
    static int env_seq;
    Inst* in = (Inst*)calloc(1, sizeof(Inst));
    in->fd = -1;
    in->fobs = obs;
    setenv("NH_ZT_MASK", "1", 0); // the env's zero-time mask: the challenge ends an episode after 10,000 clock-less steps
    { // the env builds its per-env hackdir from NETHACKDIR; stock panics on the fork's dungeon file
      // ("Dungeon description not valid", how_done 11, every game scores 0), so refuse anything but the stock data dir
        static int checked;
        if (!checked) {
            const char* nd = getenv("NETHACKDIR");
            char want[4400], libdir[4200]; snprintf(libdir, sizeof libdir, "%s", stock_lib_path());
            char* slash = strrchr(libdir, '/'); if (slash) *slash = 0;
            snprintf(want, sizeof want, "%s/nethackdir", libdir);
            char rn[PATH_MAX], rw[PATH_MAX];
            if (!nd || !realpath(nd, rn) || !realpath(want, rw) || strcmp(rn, rw) != 0) {
                fprintf(stderr, "nh_stock: NETHACKDIR must be the stock data dir %s (got %s); refusing to run the stock engine on the fork's data\n", want, nd ? nd : "(unset)");
                exit(2);
            }
            checked = 1;
        }
    }
    if (inst_open_lib(in) != 0) exit(1);
    nh_patch_got(in);
    wire_obs(in, obs);
    memset(&in->sset, 0, sizeof in->sset);
    snprintf(in->sset.hackdir, sizeof in->sset.hackdir, "%s", set->hackdir);
    // NLE's own option string (nle/nethack/nethack.py NETHACKOPTIONS, plus a random character): the NetHack Challenge interface.
    // Passed verbatim, as NLE passes it; NH_STOCK_OPTIONS overrides. The env's rc file (set->options) is not used: stock fills
    // blstats from the status line, so the fork's !status_updates does not apply.
    { const char* o = getenv("NH_STOCK_OPTIONS"); snprintf(in->sset.options, sizeof in->sset.options, "%s", o && *o ? o : NH_STOCK_DEFAULT_OPTIONS); }
    { static int shown_opts; if (__sync_bool_compare_and_swap(&shown_opts, 0, 1)) fprintf(stderr, "nh_stock: OPTIONS=%s\n", in->sset.options); }
    in->sset.spawn_monsters = set->spawn_monsters;
    in->ch_steps = 0; in->ch_noprog = 0; in->ch_maxnoprog = 0; in->ch_turn = -1; in->ch_aborted = 0; in->ep_logged = 0;
    sseed_t seed = {{set->initial_seeds.seeds[0], set->initial_seeds.seeds[1]}, 0};
    in->seed0 = seed.seeds[0];
    if (guarded_start(in, set->initial_seeds.use_init_seeds ? &seed : NULL)) { obs->done = 1; obs->how_done = -1; return (nle_ctx_t*)in; }
    sync_status(in, obs);
    if (in->so.done) { // the engine exited during start-up: hand the env a finished episode, touch nothing else
        static long n_startdead; long k = __sync_add_and_fetch(&n_startdead, 1);
        if (k <= 3) { fprintf(stderr, "nh_stock: game ended during start-up (#%ld, how_done=%d) hackdir=%s\n", k, in->so.how_done, in->sset.hackdir); for (int r = 0; r < 6; r++) fprintf(stderr, "  tty[%d] %.78s\n", r, in->so.tty_chars + r * TTY_CO); fprintf(stderr, "  msg: %.120s\n", in->so.message); }
        obs->done = 1; obs->how_done = -1;
        return (nle_ctx_t*)in;
    }
    unsigned dseed = (unsigned)(set->initial_seeds.seeds[0] ^ (unsigned long)(__sync_add_and_fetch(&env_seq, 1) * 7919));
    dr_reset(&in->S, &in->d, dseed);
    dr_identity_from_text(&in->S, &in->d);
    { char msg[256]; dr_msg(&in->d, msg, sizeof msg); dr_update_memory(&in->S, &in->d, msg); dr_track_path(&in->S, &in->d, -1); }
    topl_save(in);
    if (!in->so.done && !dr_prompt_open(&in->d)) { dr_probe_discoveries(&in->S, &in->d, in, stock_send); in->S.disc_time_probed = 1; }
    if (obs->inv_state) memset(obs->inv_state, 0, INV * NLE_INV_STATE_FIELDS);
    if (obs->inv_true_glyphs) for (int i = 0; i < INV; i++) obs->inv_true_glyphs[i] = NO_GLYPH;
    in->mapped = 0;
    return (nle_ctx_t*)in;
}

static void ep_log(Inst* in, int how) { // NH_EPLOG=<file>: one line per finished episode in completion order: score how turn worst_clockless_run role race gender
    static FILE* f; static int init; if (!init) { init = 1; const char* v = getenv("NH_EPLOG"); if (v) f = fopen(v, "a"); }
    if (in->ep_logged || !f) return; in->ep_logged = 1;
    fprintf(f, "%ld %d %ld %ld %d %d %d\n", in->last_bl[9], how, in->last_bl[20], in->ch_maxnoprog, in->S.role, in->S.race, in->S.gender); fflush(f);
}
nle_ctx_t* nle_step(nle_ctx_t* c, nle_obs* obs) {
    Inst* in = (Inst*)c;
    if (in->so.done) { obs->done = 1; return c; } // finished coroutine: the env must reset, not step
    wire_obs(in, obs); // the env may re-bind any output buffer between calls (multi-buffer pipeline): always write where it reads
    int key = obs->action;
    if (in->vmore) { // the fork is showing --More-- here: keys other than space/Enter/ESC are eaten, the dismissal reveals the text the turn produced (nothing after ESC: WIN_STOP)
        int dis = key == ' ' || key == 13 || key == 10 || key == 27;
        if (dis) { in->vmore = 0; const char* t = key == 27 ? "" : in->vmore_text; if (in->d.message) { memset(in->d.message, 0, 256); snprintf((char*)in->d.message, 256, "%s", t); } if (in->d.misc) in->d.misc[2] = 0; }
        goto vmore_skip; }
    in->so.action = key;
    in->S.count_pending = (key >= (int)'0' && key <= (int)'9'); // a count prefix is being typed: no probe may come between its digits and the command
    if (in->d.blstats && in->d.blstats[20] > 0) memcpy(in->last_bl, in->d.blstats, sizeof in->last_bl);
    if (guarded_step(in)) { sync_status(in, obs); obs->done = 1; obs->how_done = -1; ep_log(in, -1); return c; } // full stock fill: glyph buffers hold true glyphs again
vmore_skip:
    in->mapped = 0;
    sync_status(in, obs);
    if (!in->so.done && !in->vmore) nh_answer_getpos(in);
    topl_save(in);
    int stalled = dr_after_key(&in->S, &in->d, in, stock_send, key, in->so.done);
    if (!in->so.done && !stalled) {
        // a move inside a multi-key env step (e.g. [move, e, y, Enter] ending blind): the fork's arrival look happened at the move,
        // so derive now while the hero can still see; the boundary (nle_obs_refresh) then reuses this cell
        if (dr_hero_moved(&in->S, &in->d) && !dr_prompt_open(&in->d) && !in->S.count_pending && in->d.blstats && !(in->d.blstats[25] & 0x220)) dr_boundary(&in->S, &in->d, in, stock_send); // only when a look can actually run, else the boundary keeps 'moved'
    }
    topl_restore(in);
    if (!in->so.done && (in->ch_steps >= 1000000 || in->ch_noprog >= 10000)) { in->ch_aborted = 1; in->so.done = 1; in->so.how_done = 13; obs->done = 1; obs->how_done = 13; } // NetHackChallenge: max_episode_steps 1e6, no_progress_timeout 10,000 steps
    if (stalled) { // a million clock-less keys: end the episode as truncated (the gym binding does the same)
        static long n_trunc; if (__sync_add_and_fetch(&n_trunc, 1) <= 3) fprintf(stderr, "nh_stock: truncated at T=%ld after %d keys without game time\n", in->d.blstats ? in->d.blstats[20] : -1L, DR_STALL_CAP);
        obs->done = 1; obs->how_done = -1;
    }
    if (obs->done) ep_log(in, obs->how_done);
    return c;
}

// step boundary: probes, every derived hook value, then the glyph export (bijection + hero tile + engraving bits)
nle_ctx_t* nle_obs_refresh(nle_ctx_t* c, nle_obs* obs) {
    Inst* in = (Inst*)c;
    if (in->so.glyphs != (obs->glyphs ? obs->glyphs : in->glyphs) || in->so.blstats != (obs->blstats ? obs->blstats : in->blstats) || in->so.message != (obs->message ? obs->message : in->message)) wire_obs(in, obs);
    sync_status(in, obs);
    if (obs->done) return c;
    if (in->mapped) return c; // a second refresh without a key in between: nothing new to derive
    topl_save(in);
    dr_boundary(&in->S, &in->d, in, stock_send);
    topl_restore(in);
    dr_export_glyphs(&in->S, &in->d, 1);
    in->mapped = 1;
    return c;
}

void nle_end(nle_ctx_t* c) {
    Inst* in = (Inst*)c;
    if (!in) return;
    if (in->ctx && in->s_end && !in->crashed) in->s_end(in->ctx); // a faulted engine is abandoned (its stack leaks), never re-entered
    inst_close_lib(in);
    free(in);
}

void nle_identity(nle_ctx_t* c, int* r, int* rc, int* g, int* a) {
    Inst* in = (Inst*)c;
    *r = in->S.role; *rc = in->S.race; *g = in->S.gender; *a = in->S.align;
}

int nle_path_drain(nle_ctx_t* c, short* p, int n) {
    Inst* in = (Inst*)c;
    int m = n < in->S.path_n ? n : in->S.path_n;
    memcpy(p, in->S.path, 2 * (size_t)m * sizeof(short));
    in->S.path_n = 0;
    return m;
}

// ---------------------------------------------------------------- fork-only hooks, from the derived state
long nle_shop_price(nle_ctx_t* c) { return ((Inst*)c)->S.price; }
int nle_terrain_underfoot(nle_ctx_t* c) { return ((Inst*)c)->S.terrain; }
int nle_inside_shop(nle_ctx_t* c) { return ((Inst*)c)->S.inshop; }
int nle_container_at(nle_ctx_t* c) { return ((Inst*)c)->S.cont; }
int nle_food_underfoot(nle_ctx_t* c) { return ((Inst*)c)->S.food; }
int nle_discoveries(nle_ctx_t* c) { (void)c; return 0; }
int nle_peaceful_at(nle_ctx_t* c, int x, int y) { Inst* in = (Inst*)c; return (x >= 1 && x < 80 && y >= 0 && y < 21) ? in->S.peace[y * 79 + (x - 1)] : 0; }
int nle_lnc_bits(nle_ctx_t* c) { return ((Inst*)c)->S.lnc; }
void nle_weight(nle_ctx_t* c, int* wt, int* cap) { Inst* in = (Inst*)c; *wt = in->S.wt; *cap = in->S.cap; }
int nle_spells(nle_ctx_t* c, short* a, signed char* b, signed char* d, int* e, int n) {
    Inst* in = (Inst*)c; int m = n < in->S.nsp ? n : in->S.nsp;
    for (int i = 0; i < m; i++) { a[i] = in->S.sp_ids[i]; b[i] = in->S.sp_levs[i]; d[i] = in->S.sp_fails[i]; e[i] = in->S.sp_knows[i]; }
    return m;
}
int nle_cast_blocked(nle_ctx_t* c) { return ((Inst*)c)->S.castblk; }
int nle_intrinsics(nle_ctx_t* c) { return ((Inst*)c)->S.intr; }
