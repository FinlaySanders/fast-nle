def patch(s):
 a='    unsigned short obj_mem[NH_GRID];'
 assert s.count(a)==1
 s=s.replace(a,'''    int token_cache_valid;
    long token_cache_x, token_cache_y;
    short token_cache_glyphs[NH_GRID];
    unsigned char token_cache_mon[NETHACK_V3_K * NETHACK_V3_MONF];
    unsigned char token_cache_item[NETHACK_V3_K * NETHACK_V3_ITEMF];
'''+a)
 a='memset(env->obj_mem, 0, sizeof(env->obj_mem));'
 assert s.count(a)==2;s=s.replace(a,a+' env->token_cache_valid = 0;')
 a='''        long hx = env->blstats[NLE_BL_X], hy = env->blstats[NLE_BL_Y];
'''
 assert s.count(a)==1
 s=s.replace(a,a+'''        if (env->token_cache_valid && hx == env->token_cache_x && hy == env->token_cache_y
            && !memcmp(env->glyphs, env->token_cache_glyphs, sizeof(env->token_cache_glyphs))) {
            unsigned char* cached_mp = ((obs_t*)env->agents[0].observations) + NETHACK_OFF_TOKM;
            unsigned char* cached_ip = ((obs_t*)env->agents[0].observations) + NETHACK_OFF_TOKI;
            memcpy(cached_mp, env->token_cache_mon, sizeof(env->token_cache_mon));
            memcpy(cached_ip, env->token_cache_item, sizeof(env->token_cache_item));
            for (int k = 0; k < NETHACK_V3_K; k++) {
                unsigned char* e = cached_mp + k * NETHACK_V3_MONF;
                if (!(e[0] | e[1])) break;
                int pet = e[4] & 8;
                int peace = pet || nle_peaceful_at(env->ctx,
                    (int)hx + (signed char)e[2] + 1, (int)hy + (signed char)e[3]);
                e[4] = (e[4] & 12) | (peace ? 2 : 1);
            }
        } else {
''')
 a='''    }
    // topline
'''
 assert s.count(a)==1
 b='''            memcpy(env->token_cache_glyphs, env->glyphs, sizeof(env->token_cache_glyphs));
            memcpy(env->token_cache_mon, mp, sizeof(env->token_cache_mon));
            memcpy(env->token_cache_item, ip, sizeof(env->token_cache_item));
            env->token_cache_x = hx; env->token_cache_y = hy;
            env->token_cache_valid = hx >= 0 && hx < NH_COLS && hy >= 0 && hy < NH_ROWS;
        }
    }
    // topline
'''
 return s.replace(a,b)
