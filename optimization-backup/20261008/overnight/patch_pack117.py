def patch(s):
 a='''    if (!(verb->item_classes & (1u << env->inv_oclasses[i]))) return 0;
'''
 assert s.count(a)==1;s=s.replace(a,'')
 b='''static int nethack_slot_usable(const Nethack* env, const Verb* verb, int i) {
'''
 assert s.count(b)==1;return s.replace(b,b+a)
