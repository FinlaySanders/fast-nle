// Freeze the wall clock for the process. NetHack consults time()/localtime() for
// moon phase, night, Friday 13th and u.ubirthday; the fork and the C stock backend
// both fake them so games are reproducible, and the challenge environment does not.
#define _GNU_SOURCE
#include <time.h>
#include <string.h>
#define FIXED 1600000000L
time_t time(time_t* t) { if (t) *t = (time_t)FIXED; return (time_t)FIXED; }
static struct tm g_tm;
static struct tm* fill(struct tm* o) {
    memset(o, 0, sizeof *o);
    o->tm_year = 120; o->tm_mon = 8; o->tm_mday = 13; o->tm_hour = 12;
    o->tm_wday = 0; o->tm_yday = 256; o->tm_isdst = 0;
    return o;
}
struct tm* localtime(const time_t* t) { (void)t; return fill(&g_tm); }
struct tm* localtime_r(const time_t* t, struct tm* r) { (void)t; return fill(r); }
struct tm* gmtime(const time_t* t) { (void)t; return fill(&g_tm); }
