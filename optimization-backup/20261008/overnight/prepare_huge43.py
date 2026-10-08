from pathlib import Path
import shutil,subprocess,difflib
r=Path(__file__).parent;s=r/'engine-source';b=r/'huge43-before';b.mkdir()
for rel in ['tools/gen_ctx.py','src/nh_ctx_gen.c']:
 p=b/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/rel,p)
p=s/'tools/gen_ctx.py';t=p.read_text()
a='''    out.append("    size_t nh_sz = (sizeof(struct nh_ctx) + 4095) & ~(size_t) 4095;")
    out.append("    struct nh_ctx *nh = (struct nh_ctx *) mmap(")
    out.append("        NULL, nh_sz, PROT_READ | PROT_WRITE,")
    out.append("        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);")
    out.append("    if (nh == MAP_FAILED)")
    out.append("        return (struct nh_ctx *) 0;")'''
c='''#if defined(__linux__) && defined(MADV_HUGEPAGE)
    size_t align = 2 * 1024 * 1024;
    size_t nh_sz = (sizeof(struct nh_ctx) + align - 1) & ~(align - 1);
    char *raw = mmap(NULL, nh_sz + align, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    struct nh_ctx *nh;
    size_t prefix, suffix;
    if (raw == MAP_FAILED)
        return (struct nh_ctx *) 0;
    prefix = (align - ((size_t) raw & (align - 1))) & (align - 1);
    nh = (struct nh_ctx *) (raw + prefix);
    suffix = align - prefix;
    if (prefix) munmap(raw, prefix);
    if (suffix) munmap((char *) nh + nh_sz, suffix);
    madvise(nh, nh_sz, MADV_HUGEPAGE);
#else
    size_t nh_sz = (sizeof(struct nh_ctx) + 4095) & ~(size_t) 4095;
    struct nh_ctx *nh = (struct nh_ctx *) mmap(
        NULL, nh_sz, PROT_READ | PROT_WRITE,
        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (nh == MAP_FAILED)
        return (struct nh_ctx *) 0;
#endif'''
z='\n'.join('    out.append('+repr(line)+')' for line in c.splitlines())
assert t.count(a)==1;t=t.replace(a,z)
a='    out.append("    munmap(nh, (sizeof(struct nh_ctx) + 4095) & ~(size_t) 4095);")'
c='''#if defined(__linux__) && defined(MADV_HUGEPAGE)
    munmap(nh, (sizeof(struct nh_ctx) + 2097151) & ~(size_t) 2097151);
#else
    munmap(nh, (sizeof(struct nh_ctx) + 4095) & ~(size_t) 4095);
#endif'''
assert t.count(a)==1;t=t.replace(a,'\n'.join('    out.append('+repr(line)+')' for line in c.splitlines()));p.write_text(t)
subprocess.run(['python',str(s/'tools/gen_ctx.py')],check=True,stdout=subprocess.DEVNULL)
out=[]
for p in sorted(b.rglob('*')):
 if p.is_file():
  rel=p.relative_to(b);out.extend(difflib.unified_diff(p.read_text().splitlines(True),(s/rel).read_text().splitlines(True),fromfile='a/'+str(rel),tofile='b/'+str(rel)))
(r/'huge43.patch').write_text(''.join(out))
