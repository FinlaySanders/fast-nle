from pathlib import Path
import difflib
r=Path(__file__).parent;p=r/'engine-source/src/monmove.c';old=p.read_text();anchor='static NEARDATA const char gem_class[] = { GEM_CLASS, 0 };';assert old.count(anchor)==1
helper='''

static inline boolean
nh_item_class_in(unsigned char cls, unsigned int mask)
{
    return cls < 32 && ((mask >> cls) & 1U);
}
'''
new=old.replace(anchor,anchor+helper)
repls={
'index(practical, otmp->oclass)':'nh_item_class_in(otmp->oclass, 1U | (1U << WEAPON_CLASS)\n                             | (1U << ARMOR_CLASS) | (1U << GEM_CLASS) | (1U << FOOD_CLASS))',
'index(magical, otmp->oclass)':'nh_item_class_in(otmp->oclass, 1U | (1U << AMULET_CLASS)\n                             | (1U << POTION_CLASS) | (1U << SCROLL_CLASS) | (1U << WAND_CLASS)\n                             | (1U << RING_CLASS) | (1U << SPBOOK_CLASS))',
'index(indigestion, otmp->oclass)':'nh_item_class_in(otmp->oclass, 1U | (1U << BALL_CLASS) | (1U << ROCK_CLASS))'}
for a,z in repls.items():assert new.count(a)==1;new=new.replace(a,z)
(r/'class26-before-monmove.c').write_text(old);p.write_text(new);(r/'class26.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/src/monmove.c',tofile='b/src/monmove.c')))
