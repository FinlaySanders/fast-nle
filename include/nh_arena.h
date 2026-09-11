/* fast-nle: per-game allocator behind alloc()/free(). Each game owns one
   lazily-touched 64 MB reservation with 16-byte size classes and per-class
   free lists, so a game's monsters, objects, engravings and timers sit in
   its own region instead of scattered across the process heap. Pointer
   values never reach game logic (goldens replay identically under ASLR),
   payloads are zeroed on every hand-out, and anything the arena does not
   own or cannot serve falls through to libc unchanged. */
#ifndef NH_ARENA_H
#define NH_ARENA_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct nh_arena nh_arena;
nh_arena *nh_arena_new(void);
void nh_arena_destroy(nh_arena *);
void *nh_arena_alloc_hook(unsigned int);
void nh_arena_free_hook(void *);
#ifdef __cplusplus
}
#endif
#endif
