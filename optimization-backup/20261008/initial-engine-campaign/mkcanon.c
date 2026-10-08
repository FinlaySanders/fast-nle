/* Build-time appearance table; generated from the engine's object definitions. */
#include "/puffertank/experiments/nethack-perf-20260917/engine-baseline/src/objects.c"
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *out = fopen(argv[1], "w");
    if (!out) return 1;
    int n = sizeof(objects_baseline) / sizeof(objects_baseline[0]) - 1;
    fprintf(out, "/* Generated from objects.c; do not edit. */\nstatic const short nle_appearance_canon[%d] = {\n", n + 1);
    for (int i = 0; i <= n; ++i) {
        int best = i;
        const char *desc = obj_descr_baseline[i].oc_descr;
        if (i < n && desc && desc[0]) {
            best = -1;
            for (int j = 0; j < n; ++j) {
                const struct objdescr *d = &obj_descr_baseline[j];
                if (objects_baseline[j].oc_class != objects_baseline[i].oc_class || !d->oc_descr || strcmp(desc, d->oc_descr)) continue;
                if (best < 0) best = j;
                if (objects_baseline[j].oc_class == GEM_CLASS && d->oc_name && !strncmp(d->oc_name, "worthless", 9)) best = j;
            }
            if (best < 0) best = i;
        }
        fprintf(out, "%d,%s", best, i % 16 == 15 ? "\n" : " ");
    }
    fprintf(out, "\n};\n");
    return fclose(out) != 0;
}
