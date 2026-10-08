def patch(s):
 a='''        for (int k = 0; k < NETHACK_V3_K && k < nmon; k++) {
            int best = -1, bd = 1 << 30;'''
 b='''        int mon_distance[256];
        for (int i = 0; i < nmon; i++) {
            int dx = mon_cell[i] % NH_COLS - (int)hx;
            int dy = mon_cell[i] / NH_COLS - (int)hy;
            mon_distance[i] = abs(dx) > abs(dy) ? abs(dx) : abs(dy);
        }
        for (int k = 0; k < NETHACK_V3_K && k < nmon; k++) {
            int best = -1, bd = 1 << 30;'''
 assert s.count(a)==1;s=s.replace(a,b)
 a='''                int dx = mon_cell[i] % NH_COLS - (int)hx, dy = mon_cell[i] / NH_COLS - (int)hy;
                int d = abs(dx) > abs(dy) ? abs(dx) : abs(dy);'''
 b='''                int d = mon_distance[i];'''
 assert s.count(a)==1;return s.replace(a,b)
