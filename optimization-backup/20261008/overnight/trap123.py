from pathlib import Path
import subprocess,difflib
r=Path(__file__).parent;s=r/'engine-source'
files=['include/nh_ctx_gen.h','tools/globals.def','src/trap.c','src/save.c','src/restore.c','src/mkmaze.c']
before={n:(s/n).read_text() for n in files}
for n,t in before.items():assert t==(r/'pgo61-source'/n).read_text(),n
after=dict(before)
def sub(n,a,b):
 assert after[n].count(a)==1,(n,a);after[n]=after[n].replace(a,b)
sub('include/nh_ctx_gen.h','    unsigned char g_nh_no_hero_gold;', '    int g_nh_trap_valid;\n    unsigned char g_nh_trap_bits[COLNO][(ROWNO+7)/8];\n    unsigned char g_nh_no_hero_gold;')
sub('include/nh_ctx_gen.h','#define nh_no_hero_gold (nh_cur->g_nh_no_hero_gold)', '#define nh_no_hero_gold (nh_cur->g_nh_no_hero_gold)\n#define nh_trap_valid (nh_cur->g_nh_trap_valid)\n#define nh_trap_bits (nh_cur->g_nh_trap_bits)')
after['tools/globals.def']+='\nglobal | cold | int | nh_trap_valid | | 0\nglobal | cold | unsigned char | nh_trap_bits | [COLNO][(ROWNO+7)/8] | 0\n'
sub('src/mkmaze.c','                btrap->ty = cons->y;','                btrap->ty = cons->y;\n                nh_trap_valid = 0;')
sub('src/restore.c','    ftrap = 0;','    ftrap = 0;\n    nh_trap_valid = 0;')
sub('src/save.c','        ftrap = 0;','        ftrap = 0;\n        nh_trap_valid = 0;')
sub('src/trap.c','        ftrap = ttmp;','        ftrap = ttmp;\n        nh_trap_valid = 0;')
sub('src/trap.c','    if (Sokoban && (trap->ttyp == PIT || trap->ttyp == HOLE))','    nh_trap_valid = 0;\n    if (Sokoban && (trap->ttyp == PIT || trap->ttyp == HOLE))')
a='''    register struct trap *trap = ftrap;

    while (trap) {
        if (trap->tx == x && trap->ty == y)
            return trap;
        trap = trap->ntrap;
    }
    return (struct trap *) 0;'''
b='''    register struct trap *trap;
    if ((unsigned)x < COLNO && (unsigned)y < ROWNO) {
        if (!nh_trap_valid) {
            memset(nh_trap_bits, 0, sizeof(nh_trap_bits));
            for (trap = ftrap; trap; trap = trap->ntrap)
                if ((unsigned)trap->tx < COLNO && (unsigned)trap->ty < ROWNO)
                    nh_trap_bits[trap->tx][trap->ty >> 3] |= 1u << (trap->ty & 7);
            nh_trap_valid = 1;
        }
        if (!(nh_trap_bits[x][y >> 3] & (1u << (y & 7)))) {
#ifdef NLE_TRAP_VERIFY
            for (trap = ftrap; trap; trap = trap->ntrap)
                if (trap->tx == x && trap->ty == y) panic("trap negative-cache mismatch");
#endif
            return (struct trap *)0;
        }
    }
    for (trap = ftrap; trap; trap = trap->ntrap)
        if (trap->tx == x && trap->ty == y) return trap;
    return (struct trap *)0;'''
sub('src/trap.c',a,b)
(r/'trap123.patch').write_text(''.join(''.join(difflib.unified_diff(before[n].splitlines(True),after[n].splitlines(True),fromfile='a/'+n,tofile='b/'+n)) for n in files))
try:
 for n,t in after.items():(s/n).write_text(t)
 subprocess.run(['python',str(r/'engine_screen_alloc62.py'),'trap123'],check=True)
finally:
 for n,t in before.items():(s/n).write_text(t)
