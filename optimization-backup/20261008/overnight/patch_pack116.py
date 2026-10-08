def patch(s):
 a='''                if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
            } else if'''
 b='''                if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
                continue;
            } else if'''
 assert s.count(a)==1;return s.replace(a,b)
