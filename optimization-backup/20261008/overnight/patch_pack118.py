def patch(s):
 a='''    // WIELD while welded (known-cursed wield) refuses for free and the weld
    // never expires; the revealing first attempt on unknown BUC stays legal
    if (verb == &NETHACK_VERBS[NETHACK_ACT_WIELD]) {
        for (int j = 0; j < NETHACK_INV_SLOTS && env->inv_letters[j]; j++)
            if ((env->inv_state[j * NLE_INV_STATE_FIELDS + 5] & 2)
                && env->inv_state[j * NLE_INV_STATE_FIELDS + 0] == 1)
                return 0;
    }
'''
 assert s.count(a)==1
 assert s.count('nethack_slot_usable(')==2
 assert '&& !(a == NETHACK_ACT_WIELD && welded)' in s
 return s.replace(a,'    // The caller checks known-cursed wielding once before visiting slots.\n')
