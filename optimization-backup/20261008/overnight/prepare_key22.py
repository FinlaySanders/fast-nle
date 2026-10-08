from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/nle.c';old=p.read_text();a='    nh_cur = (struct nh_ctx *) nle->nh;\n    nh_fobj_invalidate();\n    nle->observation = obs;';z='    nh_cur = (struct nh_ctx *) nle->nh;\n    nle->observation = obs;';assert old.count(a)==1;new=old.replace(a,z);(r/'key22-before-nle.c').write_text(old);p.write_text(new);(r/'key22.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/nle.c',tofile='b/src/nle.c')))
