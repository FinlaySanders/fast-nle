import sys, statistics as st
burn, want = 4000, 10000
for name in sys.argv[1:]:
    rows = [l.split() for l in open(name) if l.strip()]
    sc = [int(r[0]) for r in rows]; n = len(sc)
    post = sc[burn:burn + want]
    def ms(x): return (st.mean(x), st.pstdev(x) / len(x) ** 0.5) if len(x) > 1 else (float('nan'), float('nan'))
    m_all, se_all = ms(sc); m_post, se_post = ms(post)
    print(f"{name.split('/')[-1]}: episodes={n} raw mean={m_all:.0f} (se {se_all:.0f})  burn-in-adjusted (drop first {burn}, next {len(post)}): mean={m_post:.0f} (se {se_post:.0f}) median={st.median(post) if post else float('nan'):.0f}")
