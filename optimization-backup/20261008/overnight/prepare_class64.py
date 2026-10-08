from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';s=p.read_text();u=s
for name,classes in [('practical',['WEAPON_CLASS','ARMOR_CLASS','GEM_CLASS','FOOD_CLASS']),('magical',['AMULET_CLASS','POTION_CLASS','SCROLL_CLASS','WAND_CLASS','RING_CLASS','SPBOOK_CLASS']),('indigestion',['BALL_CLASS','ROCK_CLASS'])]:
 old='index('+name+', otmp->oclass)';assert u.count(old)==1
 # strchr/index also matches the terminating NUL; preserve that for every char value.
 new='('+' || '.join('otmp->oclass == '+x for x in ['0']+classes)+')';u=u.replace(old,new)
shutil.copy2(p,r/'class64-before-monmove.c');p.write_text(u);(r/'class64.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),u.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
