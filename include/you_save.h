#ifndef YOU_SAVE_H
#define YOU_SAVE_H
#include <stddef.h>
_Static_assert(sizeof(struct prop) == 12, "compact property size");
_Static_assert(offsetof(struct you, uprops) == offsetof(struct you_legacy, uprops), "hero prefix layout");
_Static_assert(sizeof(struct you) - offsetof(struct you, umconf) == sizeof(struct you_legacy) - offsetof(struct you_legacy, umconf), "hero suffix layout");
static inline void you_to_legacy(struct you_legacy *out, const struct you *in) {
    memcpy(out, in, offsetof(struct you, uprops));
    for (int i = 0; i <= LAST_PROP; ++i) {
        out->uprops[i].extrinsic = in->uprops[i].extrinsic;
        out->uprops[i].blocked = in->uprops[i].blocked;
        out->uprops[i].intrinsic = in->uprops[i].intrinsic;
    }
    memcpy(&out->umconf, &in->umconf, sizeof(*in) - offsetof(struct you, umconf));
}
static inline void you_from_legacy(struct you *out, const struct you_legacy *in) {
    memcpy(out, in, offsetof(struct you, uprops));
    for (int i = 0; i <= LAST_PROP; ++i) {
        out->uprops[i].extrinsic = in->uprops[i].extrinsic;
        out->uprops[i].blocked = in->uprops[i].blocked;
        out->uprops[i].intrinsic = in->uprops[i].intrinsic;
    }
    memcpy(&out->umconf, &in->umconf, sizeof(*out) - offsetof(struct you, umconf));
}
#endif
