from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/track.c';old=p.read_text();a='''    if (full)
        nh_track_adjust(&utrack[utpnt], -1);''';b='''    if (full && utrack[utpnt].x == u.ux && utrack[utpnt].y == u.uy) {
        utpnt++;
        return;
    }
    if (full)
        nh_track_adjust(&utrack[utpnt], -1);''';assert old.count(a)==1
new=old.replace(a,b);backup=r/'track45-before-track.c';assert not backup.exists();backup.write_text(old);p.write_text(new);(r/'track45.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/track.c',tofile='b/src/track.c')))
