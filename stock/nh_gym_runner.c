// Policy runner for the gym binding: the PufferLib NetHack env plus the CPU
// forward pass, exposed to Python. The engine underneath is nh_gym_backend.c,
// which turns every keystroke into an env.step() on NetHackChallenge-v0.
#define main nh_demo_main
#include "ocean/nethack/nethack.c"
#undef main

static NethackNet* g_net;
static Nethack g_env;
static float g_acts[DEMO_NUM_HEADS];
static float g_ep_score, g_ep_len, g_ep_depth, g_ep_xp, g_ep_gt;

int nhg_open(const char* weights, unsigned seed) {
    Weights* w = load_weights((char*)weights);
    if (!w) return -1;
    g_net = make_nethack_net(w);
    nethack_color_sink = demo_colors;
    nethack_invstr_sink = demo_inv_strs;
    srand(seed);
    env_open(&g_env);           // -> puf_reset -> nle_start -> the Python reset callback
    return 0;
}

// one policy step: forward + mask + sample + the whole key macro it expands to
int nhg_policy_step(double* out) {
    demo_step_once(g_net, &g_env, g_acts, &g_ep_score, &g_ep_len, &g_ep_depth, &g_ep_xp, &g_ep_gt);
    if (out) {
        out[0] = g_env.log.n;
        out[1] = g_env.log.score;
        out[2] = g_env.log.max_depth;
        out[3] = g_env.log.episode_length;
        out[4] = g_env.log.game_time;
        out[5] = g_env.log.max_xp_level;
        out[6] = (double)g_env.agents[0].terminals[0];
        out[7] = (double)g_env.role_idx;
    }
    return (int)g_env.log.n;
}

int nhg_identity(int* role, int* race, int* gender, int* align) {
    nle_identity(g_env.ctx, role, race, gender, align);
    return 0;
}
long nhg_blstat(int i) { return (i >= 0 && i < NLE_BLSTATS_SIZE) ? g_env.blstats[i] : -1; }
void nhg_close(void) { env_close(&g_env); }
