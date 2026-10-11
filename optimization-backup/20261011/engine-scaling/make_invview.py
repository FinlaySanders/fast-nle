# invview = <base> + inventory state/true-glyph export as a materialized view: computed in update_inventory_method (the game's own
# "inventory display changed" hook) and when the discoveries generation changes, copied per step instead of walking invent twice.
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'misc1'
dst=CS/'invview/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
p=dst/'win/rl/winrl.cc'; s=p.read_text()
def rep(old,new,count=1):
    global s; assert s.count(old)==count,(s.count(old),old[:70]); s=s.replace(old,new)
# members + method decl
rep("    std::array<unsigned char, NLE_INVENTORY_SIZE> inv_oclasses_cache_;\n",
    "    std::array<unsigned char, NLE_INVENTORY_SIZE> inv_oclasses_cache_;\n    std::array<signed char, NLE_INVENTORY_SIZE * NLE_INV_STATE_FIELDS> inv_state_cache_;\n    std::array<short, NLE_INVENTORY_SIZE> inv_true_cache_;\n    unsigned inv_disc_gen_seen_ = 0;\n")
rep("    void update_inventory_method();\n","    void update_inventory_method();\n    void refresh_inv_state();\n")
rep("    inv_oclasses_cache_.fill(MAXOCLASSES);\n","    inv_oclasses_cache_.fill(MAXOCLASSES);\n    inv_state_cache_.fill(0);\n    inv_true_cache_.fill(NO_GLYPH);\n",2)
# cut the per-step derivation out of fill_obs
a=s.index("    if (obs->inv_state && !nle_partial) {"); b=s.index("    if (obs->screen_descriptions && !nle_partial) {")
body=s[a:b]
# body: inv_state block + inv_true_glyphs block. Build the method from it.
m=body.replace("    if (obs->inv_state && !nle_partial) {","    {",1)
m=m.replace("    if (obs->inv_true_glyphs && !nle_partial) {","    {",1)
m=m.replace("obs->inv_state","inv_state_cache_.data()").replace("obs->inv_true_glyphs","inv_true_cache_.data()")
method="""
/* Materialized view of the identification-gated inventory state and true glyphs.
   Rebuilt by update_inventory_method (every inventory display change) and when
   the discoveries generation moves; fill_obs copies it. Flag reads only, no RNG. */
void
NetHackRL::refresh_inv_state()
{
    inv_disc_gen_seen_ = disc_gen_;
"""+m+"}\n"
new_fill="""    if (obs->inv_state && !nle_partial) {
        if (inv_disc_gen_seen_ != disc_gen_)
            refresh_inv_state();
#ifdef NLE_INVVIEW_VERIFY
        {
            std::array<signed char, NLE_INVENTORY_SIZE * NLE_INV_STATE_FIELDS> st_saved = inv_state_cache_;
            std::array<short, NLE_INVENTORY_SIZE> tg_saved = inv_true_cache_;
            refresh_inv_state();
            if (st_saved != inv_state_cache_ || tg_saved != inv_true_cache_) {
                int slot = -1, field = -1;
                for (int k = 0; k < NLE_INVENTORY_SIZE * NLE_INV_STATE_FIELDS && slot < 0; ++k)
                    if (st_saved[k] != inv_state_cache_[k]) { slot = k / NLE_INV_STATE_FIELDS; field = k % NLE_INV_STATE_FIELDS; }
                for (int k = 0; k < NLE_INVENTORY_SIZE && slot < 0; ++k)
                    if (tg_saved[k] != inv_true_cache_[k]) { slot = k; field = 99; }
                fprintf(stderr, "INVVIEW_MISMATCH turn=%ld slot=%d field=%d\\n", moves, slot, field);
            }
        }
#endif
        std::memcpy(obs->inv_state, inv_state_cache_.data(), inv_state_cache_.size());
    }
    if (obs->inv_true_glyphs && !nle_partial) {
        if (inv_disc_gen_seen_ != disc_gen_)
            refresh_inv_state();
        std::memcpy(obs->inv_true_glyphs, inv_true_cache_.data(), sizeof(short) * NLE_INVENTORY_SIZE);
    }
"""
s=s[:a]+new_fill+s[b:]
# rebuild the view whenever the inventory list is rebuilt
rep("""        inv_oclasses_cache_[i] = inventory_[i].object_class;
    }
}""","""        inv_oclasses_cache_[i] = inventory_[i].object_class;
    }
    refresh_inv_state();
}"""+method)
p.write_text(s)
print('invview source ready (base', BASE+')'); print('method lines:', method.count('\n'))
