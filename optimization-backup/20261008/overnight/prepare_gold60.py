from pathlib import Path
import shutil,difflib,subprocess
r=Path(__file__).parent;s=r/'engine-source';b=r/'gold60-before';b.mkdir();rels=['src/steal.c','src/invent.c','src/mkobj.c','src/restore.c','tools/globals.def','include/nh_ctx_gen.h','src/nh_ctx_gen.c']
for rel in rels:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/globals.def';p.write_text(p.read_text()+'\nglobal | cold | unsigned char | nh_no_hero_gold | | 0\n')
p=s/'src/steal.c';t=p.read_text();a='''    while (chain && chain->otyp != GOLD_PIECE)
        chain = chain->nobj;
    return chain;''';z='''    boolean hero_chain = (chain == invent);
    if (hero_chain && nh_no_hero_gold) {
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
    if (hero_chain && !chain)
        nh_no_hero_gold = 1;
    return chain;''';assert t.count(a)==1;p.write_text(t.replace(a,z))
p=s/'src/invent.c';t=p.read_text();a=' added:\n    addinv_core2(obj);';assert t.count(a)==1;t=t.replace(a,' added:\n    nh_no_hero_gold = 0;\n    addinv_core2(obj);')
# Common addinv hook above covers normal additions. Cover inline insertions,
# reassignment and reorder conservatively too, including temporary extractions.
a='''reorder_invent()
{''';assert t.count(a)==1
start=t.index(a);mark=t.index('    do {',start);t=t[:mark]+'    nh_no_hero_gold = 0;\n'+t[mark:]
for a in ['        invent = goldobj;','    invent = obj;','        invent = bumped;']:
 # invent=obj also occurs inside addinv: duplicate invalidation harmless.
 assert a in t
 t=t.replace(a,a+'\n'+a[:len(a)-len(a.lstrip())]+'nh_no_hero_gold = 0;')
t=t.replace("        invent = obj;\n    nh_no_hero_gold = 0;", "        invent = obj;\n        nh_no_hero_gold = 0;")
p.write_text(t)
p=s/'src/mkobj.c';t=p.read_text();start=t.index('replace_object(obj, otmp)');end=t.index('\n}',start);part=t[start:end];a='    case OBJ_INVENT:\n';assert part.count(a)==1;part=part.replace(a,a+'        nh_no_hero_gold = 0;\n');p.write_text(t[:start]+part+t[end:])
p=s/'src/restore.c';t=p.read_text();a='    invent = restobjchn(fd, FALSE, FALSE);';assert t.count(a)==1;p.write_text(t.replace(a,a+'\n    nh_no_hero_gold = 0;'))
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for rel in rels:out.extend(difflib.unified_diff((b/rel).read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
(r/'gold60.patch').write_text(''.join(out))
