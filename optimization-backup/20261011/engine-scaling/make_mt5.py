# mt5 = <base> + S4a in m_move/should_displace: ALLOW_MDISP already implies a monster on the cell (drop the MON_AT loads);
# recent-track avoidance gated by a 9-bit mask of track positions (the RNG-drawing loop runs only on a match, exactly as before).
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt4'
dst=CS/'mt5/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('src/monmove.c',"        if (MON_AT(nx, ny) && (info[i] & ALLOW_MDISP) && !(info[i] & ALLOW_M)\n            && !undesirable_disp(mtmp, nx, ny)) {",
    "        if ((info[i] & ALLOW_MDISP) && !(info[i] & ALLOW_M) /* ALLOW_MDISP is only set with a monster there */\n            && !undesirable_disp(mtmp, nx, ny)) {")
rep('src/monmove.c',"            if (MON_AT(nx, ny) && (info[i] & ALLOW_MDISP)\n                && !(info[i] & ALLOW_M) && !better_with_displacing)\n                continue;",
    "            if ((info[i] & ALLOW_MDISP)\n                && !(info[i] & ALLOW_M) && !better_with_displacing)\n                continue;")
rep('src/monmove.c',"        register int i, j, nx, ny, nearer;\n","        register int i, j, nx, ny, nearer;\n        unsigned int trackmask;\n")
rep('src/monmove.c',"        jcnt = min(MTSZ, cnt - 1);\n","        jcnt = min(MTSZ, cnt - 1);\n        trackmask = 0; /* neighbourhood bits of the recent track: the avoidance loop (and its RNG draw) only runs on a hit */\n        for (j = 0; j < jcnt; j++)\n            trackmask |= nh_move_position_bit(omx, omy, mtmp->mtrack[j].x, mtmp->mtrack[j].y);\n")
rep('src/monmove.c',"            if (appr != 0) {\n                mtrk = &mtmp->mtrack[0];","            if (appr != 0 && (trackmask & nh_move_position_bit(omx, omy, nx, ny))) {\n                mtrk = &mtmp->mtrack[0];")
print('mt5 source ready (base', BASE+')')
