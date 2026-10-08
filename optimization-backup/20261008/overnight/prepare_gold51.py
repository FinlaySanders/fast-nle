from pathlib import Path
import shutil,subprocess,difflib
r=Path(__file__).parent;s=r/'engine-source';b=r/'gold51-before';b.mkdir();rels=['src/steal.c','src/mon.c','src/invent.c','src/mkobj.c','src/nle.c','tools/globals.def','include/nh_ctx_gen.h','src/nh_ctx_gen.c']
for rel in rels:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/globals.def';p.write_text(p.read_text()+'\nglobal | hot | unsigned char | nh_gold_absence | | 0\n')
p=s/'src/steal.c';t=p.read_text();a='''    while (chain && chain->otyp != GOLD_PIECE)
        chain = chain->nobj;
    return chain;''';z='''    boolean hero_chain = (chain == invent);
    if (hero_chain && nh_gold_absence == 2) {
#ifdef NLE_GOLD_VERIFY
        struct obj *check = chain;
        while (check && check->otyp != GOLD_PIECE)
            check = check->nobj;
        if (check)
            panic("stale hero gold absence");
#endif
        return (struct obj *) 0;
    }
    while (chain && chain->otyp != GOLD_PIECE)
        chain = chain->nobj;
    if (hero_chain && nh_gold_absence && !chain)
        nh_gold_absence = 2;
    return chain;''';assert t.count(a)==1;p.write_text(t.replace(a,z))
p=s/'src/mon.c';t=p.read_text();a=t.index('int\nmovemon()');z=t.index('\n}',a);part=t[a:z];needle='    for (mtmp = fmon; mtmp; mtmp = nmtmp) {';assert part.count(needle)==1;part=part.replace(needle,'    nh_gold_absence = 1; /* cache absence only during this movement pass */\n'+needle);needle='    if (any_light_source())';assert part.count(needle)==1;part=part.replace(needle,'    nh_gold_absence = 0;\n'+needle);p.write_text(t[:a]+part+t[z:])
p=s/'src/invent.c';t=p.read_text();a=' added:\n    addinv_core2(obj);';z=' added:\n    if (nh_gold_absence) nh_gold_absence = 1;\n    addinv_core2(obj);';assert t.count(a)==1;p.write_text(t.replace(a,z))
p=s/'src/mkobj.c';t=p.read_text();a=t.index('replace_object(obj, otmp)');z=t.index('\n}',a);part=t[a:z];needle='    case OBJ_INVENT:\n';assert part.count(needle)==1;part=part.replace(needle,needle+'        if (nh_gold_absence) nh_gold_absence = 1;\n');p.write_text(t[:a]+part+t[z:])
p=s/'src/nle.c';t=p.read_text();a='    nh_cur = (struct nh_ctx *) nle->nh;\n    nh_fobj_invalidate();\n    nle->observation = obs;';assert t.count(a)==1;p.write_text(t.replace(a,'    nh_cur = (struct nh_ctx *) nle->nh;\n    nh_gold_absence = 0;\n    nh_fobj_invalidate();\n    nle->observation = obs;'))
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for rel in rels:out.extend(difflib.unified_diff((b/rel).read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(r/'gold51.patch').write_text(''.join(out))
