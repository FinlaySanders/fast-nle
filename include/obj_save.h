#ifndef OBJ_SAVE_H
#define OBJ_SAVE_H
#include <stddef.h>
_Static_assert(sizeof(struct obj)==88,"compact object size");
_Static_assert(sizeof(struct obj_legacy)==96,"legacy object size");
_Static_assert(offsetof(struct obj,owornmask)==36,"mask occupies old padding");
_Static_assert(offsetof(struct obj,quan)==40 && offsetof(struct obj_legacy,quan)==40,"middle layout");
_Static_assert(offsetof(struct obj,oextra)==80 && offsetof(struct obj_legacy,owornmask)==80,"middle end");
static inline void obj_to_legacy(struct obj_legacy *out,const struct obj *in) {
    memset(out,0,sizeof(*out));
    memcpy(out,in,36);
    memcpy(&out->quan,&in->quan,40);
    out->owornmask=in->owornmask;
    out->oextra=in->oextra;
}
static inline void obj_from_legacy(struct obj *out,const struct obj_legacy *in) {
    memcpy(out,in,36);
    memcpy(&out->quan,&in->quan,40);
    out->owornmask=in->owornmask;
    out->oextra=in->oextra;
}
#endif
