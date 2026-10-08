def patch(s):
 a='''    static const int ray_verbs[2] = {NETHACK_ACT_THROW, NETHACK_ACT_ZAP};
    for (int v = 0; v < 2; v++) {
        unsigned char* vdirs = dirs + nethack_dir_head(ray_verbs[v]) * NETHACK_NUM_DIRS;
        int any = 0;
        for (int d = 0; d < NETHACK_NUM_DIRS; d++) {
            vdirs[d] = nethack_ray_target(env, NETHACK_DIR_DX[d], NETHACK_DIR_DY[d]);
            any |= vdirs[d];
        }
        if (!any) memset(vdirs, 1, NETHACK_NUM_DIRS);
    }'''
 b='''    unsigned char* throw_dirs = dirs + nethack_dir_head(NETHACK_ACT_THROW) * NETHACK_NUM_DIRS;
    unsigned char* zap_dirs = dirs + nethack_dir_head(NETHACK_ACT_ZAP) * NETHACK_NUM_DIRS;
    int any_ray = 0;
    for (int d = 0; d < NETHACK_NUM_DIRS; d++) {
        throw_dirs[d] = nethack_ray_target(env, NETHACK_DIR_DX[d], NETHACK_DIR_DY[d]);
        any_ray |= throw_dirs[d];
    }
    if (!any_ray) memset(throw_dirs, 1, NETHACK_NUM_DIRS);
    memcpy(zap_dirs, throw_dirs, NETHACK_NUM_DIRS);'''
 assert s.count(a)==1;return s.replace(a,b)
