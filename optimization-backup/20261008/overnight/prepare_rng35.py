from pathlib import Path
import shutil
r=Path(__file__).parent;p=r/'engine-source/src/rnd.c';shutil.copy2(p,r/'rng35-before-rnd.c');s=p.read_text()
table=[0,0]+[(1<<64)//n for n in range(2,256)]
helper='''#if defined(__SIZEOF_INT128__) && defined(__GNUC__)
static inline uint64_t
nh_small_mod(uint64_t value, unsigned int bound)
{
    static const uint64_t reciprocal[256] = {
'''+''.join('        '+', '.join(str(v)+'ULL' for v in table[i:i+4])+',\n' for i in range(0,256,4))+'''    };
    uint64_t quotient = (uint64_t)(((__uint128_t)value * reciprocal[bound]) >> 64);
    uint64_t remainder = value - quotient * bound;
    return remainder >= bound ? remainder - bound : remainder;
}
#endif

'''
a='''static int
RND(int x)
{
    int r = (int) (isaac64_next_uint64(nle_rng_state(CORE)) % x);'''
b=helper+'''static int
RND(int x)
{
    uint64_t value = isaac64_next_uint64(nle_rng_state(CORE));
    int r;
#if defined(__SIZEOF_INT128__) && defined(__GNUC__)
    if (!__builtin_constant_p(x) && x > 1 && x < 256)
        r = (int) nh_small_mod(value, (unsigned int)x);
    else
#endif
        r = (int) (value % x);'''
assert s.count(a)==1;p.write_text(s.replace(a,b));(r/'rng35-helper.txt').write_text(helper)
