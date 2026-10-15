#ifdef __SSE2__
#include <emmintrin.h>
#endif
/* NetHack 3.6	monmove.c	$NHDT-Date: 1575245074 2019/12/02 00:04:34 $  $NHDT-Branch: NetHack-3.6 $:$NHDT-Revision: 1.116 $ */
/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/*-Copyright (c) Michael Allison, 2006. */
/* NetHack may be freely redistributed.  See license for details. */

#include "hack.h"
#include "mfndpos.h"
#include "nh_ctx_files/engrave_c.h"
#include "nh_ctx_files/region_c.h"
#include <pthread.h> /* v1.8: eligibility mask calibration */
extern int nh_mt2_fast;
static int FDECL(dochug_fast, (struct monst *));
#define MT2_MAXOBJ 16
static int mt2_box_objects(int, int, int, int, struct obj **);
#ifdef NH_MT2_TRACE
#include <stdio.h>
#include <stdlib.h>
extern int nh_mt2_trace_elig, nh_mt2_trace_rng0;
static int mt2_trace_on(void);
extern FILE *nh_mt2_trace_fp;
#include "isaac64.h"
extern isaac64_ctx *FDECL(nle_rng_state, (int));
#endif
#include "artifact.h"


STATIC_DCL void FDECL(watch_on_duty, (struct monst *));
STATIC_DCL int FDECL(disturb, (struct monst *));
STATIC_DCL void FDECL(release_hero, (struct monst *));
STATIC_DCL void FDECL(distfleeck, (struct monst *, int *, int *, int *)) __attribute__((always_inline));
/* per-move helpers: inline into the monster-turn pass (their out-of-line copies stay for other callers) */
extern void FDECL(set_apparxy, (struct monst *)) __attribute__((always_inline));
extern boolean FDECL(should_displace, (struct monst *, coord *, long *, int, XCHAR_P, XCHAR_P)) __attribute__((always_inline));
extern boolean FDECL(m_digweapon_check, (struct monst *, XCHAR_P, XCHAR_P)) __attribute__((always_inline));
extern boolean FDECL(monhaskey, (struct monst *, BOOLEAN_P)) __attribute__((always_inline));
extern int FDECL(dochugw, (struct monst *)) __attribute__((always_inline));
STATIC_DCL int FDECL(m_arrival, (struct monst *));
STATIC_DCL boolean FDECL(stuff_prevents_passage, (struct monst *));
STATIC_DCL int FDECL(vamp_shift, (struct monst *, struct permonst *,
                                  BOOLEAN_P));

static inline boolean
nh_move_obj_at(int x, int y)
{
    boolean present = NH_SUMMARY(x, y).move_obj_present;
#ifdef NH_MOVEMENT_MASK_VERIFY
    if (present != OBJ_AT(x, y))
        panic("object presence mismatch after movement %d,%d", x, y);
#endif
    return present;
}

/* True if mtmp died */
boolean
mb_trapped(mtmp)
struct monst *mtmp;
{
    if (flags.verbose) {
        if (cansee(mtmp->mx, mtmp->my) && !Unaware)
            pline("KABOOM!!  You see a door explode.");
        else if (!Deaf)
            You_hear("a distant explosion.");
    }
    wake_nearto(mtmp->mx, mtmp->my, 7 * 7);
    mtmp->mstun = 1;
    mtmp->mhp -= rnd(15);
    if (DEADMONSTER(mtmp)) {
        mondied(mtmp);
        if (!DEADMONSTER(mtmp)) /* lifesaved */
            return FALSE;
        else
            return TRUE;
    }
    return FALSE;
}

/* check whether a monster is carrying a locking/unlocking tool */
boolean
monhaskey(mon, for_unlocking)
struct monst *mon;
boolean for_unlocking; /* true => credit card ok, false => not ok */
{
    if (for_unlocking && m_carrying(mon, CREDIT_CARD))
        return TRUE;
    return m_carrying(mon, SKELETON_KEY) || m_carrying(mon, LOCK_PICK);
}

void
mon_yells(mon, shout)
struct monst *mon;
const char *shout;
{
    if (Deaf) {
        if (canspotmon(mon))
            /* Sidenote on "A watchman angrily waves her arms!"
             * Female being called watchman is correct (career name).
             */
            pline("%s angrily %s %s %s!",
                Amonnam(mon),
                nolimbs(mon->data) ? "shakes" : "waves",
                mhis(mon),
                nolimbs(mon->data) ? mbodypart(mon, HEAD)
                                   : makeplural(mbodypart(mon, ARM)));
    } else {
        if (canspotmon(mon))
            pline("%s yells:", Amonnam(mon));
        else
            You_hear("someone yell:");
        verbalize1(shout);
    }
}

STATIC_OVL void
watch_on_duty(mtmp)
register struct monst *mtmp;
{
    int x, y;

    if (mtmp->mpeaceful && in_town(u.ux + u.dx, u.uy + u.dy)
        && mtmp->mcansee && m_canseeu(mtmp) && !rn2(3)) {
        if (picking_lock(&x, &y) && IS_DOOR(TYP_AT(x, y))
            && (NH_TILE(x, y).doormask & D_LOCKED)) {
            if (couldsee(mtmp->mx, mtmp->my)) {
                if (NH_TILE(x, y).looted & D_WARNED) {
                    mon_yells(mtmp, "Halt, thief!  You're under arrest!");
                    (void) angry_guards(!!Deaf);
                } else {
                    mon_yells(mtmp, "Hey, stop picking that lock!");
                    NH_TILE(x, y).looted |= D_WARNED;
                }
                stop_occupation();
            }
        } else if (is_digging()) {
            /* chewing, wand/spell of digging are checked elsewhere */
            watch_dig(mtmp, context.digging.pos.x, context.digging.pos.y,
                      FALSE);
        }
    }
}

#ifdef NH_MT2_CG
NH_CYC_WRAP(int, dochugw, (struct monst *), (struct monst *mtmp), dochugw_impl(mtmp), nh_cyc_dochugw)
#endif
int
NH_CYC(dochugw)(mtmp)
register struct monst *mtmp;
{
    int x = mtmp->mx, y = mtmp->my;
    boolean already_saw_mon = (!occupation || distu(x, y) > (BOLT_LIM + 1) * (BOLT_LIM + 1)) ? 0 : canspotmon(mtmp); /* unread beyond that range */
    int rd = dochug(mtmp);
#ifdef NH_MT2_TRACE
    if (nh_mt2_trace_elig && nh_mt2_trace_fp && mt2_trace_on()) fprintf(nh_mt2_trace_fp, "E%d  exit id%u rd%d rng%d\n", nh_ctx_serial, mtmp->m_id, rd, nle_rng_state(0)->n);
#endif

    /* a similar check is in monster_nearby() in hack.c */
    /* check whether hero notices monster and stops current activity */
    if (occupation && !rd && !Confusion && (!mtmp->mpeaceful || Hallucination)
        /* it's close enough to be a threat */
        && distu(x, y) <= (BOLT_LIM + 1) * (BOLT_LIM + 1)
        /* and either couldn't see it before, or it was too far away */
        && (!already_saw_mon || !couldsee(x, y)
            || distu(x, y) > (BOLT_LIM + 1) * (BOLT_LIM + 1))
        /* can see it now, or sense it and would normally see it */
        && (canseemon(mtmp) || (sensemon(mtmp) && couldsee(x, y)))
        && mtmp->mcanmove && !noattacks(mtmp->data)
        && !onscary(u.ux, u.uy, mtmp))
        stop_occupation();

    return rd;
}

boolean
onscary(x, y, mtmp)
int x, y;
struct monst *mtmp;
{
    /* creatures who are directly resistant to magical scaring:
     * Rodney, lawful minions, Angels, the Riders, shopkeepers
     * inside their own shop, priests inside their own temple */
    if (mtmp->iswiz || is_lminion(mtmp) || mtmp->data == &mons[PM_ANGEL]
        || is_rider(mtmp->data)
        || (mtmp->isshk && inhishop(mtmp))
        || (mtmp->ispriest && inhistemple(mtmp)))
        return FALSE;

    /* <0,0> is used by musical scaring to check for the above;
     * it doesn't care about scrolls or engravings or dungeon branch */
    if (x == 0 && y == 0)
        return TRUE;

    /* should this still be true for defiled/molochian altars? */
    if (IS_ALTAR(TYP_AT(x, y))
        && (mtmp->data->mlet == S_VAMPIRE || is_vampshifter(mtmp)))
        return TRUE;

    /* the scare monster scroll doesn't have any of the below
     * restrictions, being its own source of power */
    if (sobj_at(SCR_SCARE_MONSTER, x, y))
        return TRUE;

    /*
     * Creatures who don't (or can't) fear a written Elbereth:
     * all the above plus shopkeepers (even if poly'd into non-human),
     * vault guards (also even if poly'd), blind or peaceful monsters,
     * humans and elves, and minotaurs.
     *
     * If the player isn't actually on the square OR the player's image
     * isn't displaced to the square, no protection is being granted.
     *
     * Elbereth doesn't work in Gehennom, the Elemental Planes, or the
     * Astral Plane; the influence of the Valar only reaches so far.
     */
    /* NLE: all three clauses are pure predicates; test the cheap position
     * and monster-type exclusions before sengr_at, whose engraving-chain
     * walk + fuzzymatch dominated this function (mfndpos calls onscary for
     * every candidate cell of every monster; the position clause fails for
     * all but the hero's own square). Same result, no side effects. */
    return (((u.ux == x && u.uy == y)
             || (Displaced && mtmp->mux == x && mtmp->muy == y))
            && !(mtmp->isshk || mtmp->isgd || !mtmp->mcansee
                 || mtmp->mpeaceful || mtmp->data->mlet == S_HUMAN
                 || mtmp->data == &mons[PM_MINOTAUR]
                 || Inhell || In_endgame(&u.uz))
            && sengr_at("Elbereth", x, y, TRUE));
}


/* regenerate lost hit points */
void
mon_regen(mon, digest_meal)
struct monst *mon;
boolean digest_meal;
{
    if (mon->mhp < mon->mhpmax && (moves % 20 == 0 || regenerates(mon->data)))
        mon->mhp++;
    if (mon->mspec_used)
        mon->mspec_used--;
    if (digest_meal) {
        if (mon->meating) {
            mon->meating--;
            if (mon->meating <= 0)
                finish_meating(mon);
        }
    }
}

/*
 * Possibly awaken the given monster.  Return a 1 if the monster has been
 * jolted awake.
 */
STATIC_OVL int
disturb(mtmp)
register struct monst *mtmp;
{
    /*
     * + Ettins are hard to surprise.
     * + Nymphs, jabberwocks, and leprechauns do not easily wake up.
     *
     * Wake up if:
     *  in direct LOS                                           AND
     *  within 10 squares                                       AND
     *  not stealthy or (mon is an ettin and 9/10)              AND
     *  (mon is not a nymph, jabberwock, or leprechaun) or 1/50 AND
     *  Aggravate or mon is (dog or human) or
     *      (1/7 and mon is not mimicing furniture or object)
     */
    if (couldsee(mtmp->mx, mtmp->my) && distu(mtmp->mx, mtmp->my) <= 100
        && (!Stealth || (mtmp->data == &mons[PM_ETTIN] && rn2(10)))
        && (!(mtmp->data->mlet == S_NYMPH
              || mtmp->data == &mons[PM_JABBERWOCK]
#if 0 /* DEFERRED */
              || mtmp->data == &mons[PM_VORPAL_JABBERWOCK]
#endif
              || mtmp->data->mlet == S_LEPRECHAUN) || !rn2(50))
        && (Aggravate_monster
            || (mtmp->data->mlet == S_DOG || mtmp->data->mlet == S_HUMAN)
            || (!rn2(7) && M_AP_TYPE(mtmp) != M_AP_FURNITURE
                && M_AP_TYPE(mtmp) != M_AP_OBJECT))) {
        mtmp->msleeping = 0;
        return 1;
    }
    return 0;
}

/* ungrab/expel held/swallowed hero */
STATIC_OVL void
release_hero(mon)
struct monst *mon;
{
    if (mon == u.ustuck) {
        if (u.uswallow) {
            expels(mon, mon->data, TRUE);
        } else if (!sticks(youmonst.data)) {
            unstuck(mon); /* let go */
            You("get released!");
        }
    }
}

#define flees_light(mon) ((mon)->data == &mons[PM_GREMLIN]     \
                          && (uwep && artifact_light(uwep) && uwep->lamplit))
/* we could include this in the above macro, but probably overkill/overhead */
/*      && (!(which_armor((mon), W_ARMC) != 0                               */
/*            && which_armor((mon), W_ARMH) != 0))                          */

/* monster begins fleeing for the specified time, 0 means untimed flee
 * if first, only adds fleetime if monster isn't already fleeing
 * if fleemsg, prints a message about new flight, otherwise, caller should */
void
monflee(mtmp, fleetime, first, fleemsg)
struct monst *mtmp;
int fleetime;
boolean first;
boolean fleemsg;
{
    /* shouldn't happen; maybe warrants impossible()? */
    if (DEADMONSTER(mtmp))
        return;

    if (mtmp == u.ustuck)
        release_hero(mtmp); /* expels/unstuck */

    if (!first || !mtmp->mflee) {
        /* don't lose untimed scare */
        if (!fleetime)
            mtmp->mfleetim = 0;
        else if (!mtmp->mflee || mtmp->mfleetim) {
            fleetime += (int) mtmp->mfleetim;
            /* ensure monster flees long enough to visibly stop fighting */
            if (fleetime == 1)
                fleetime++;
            mtmp->mfleetim = (unsigned) min(fleetime, 127);
        }
        if (!mtmp->mflee && fleemsg && canseemon(mtmp)
            && M_AP_TYPE(mtmp) != M_AP_FURNITURE
            && M_AP_TYPE(mtmp) != M_AP_OBJECT) {
            /* unfortunately we can't distinguish between temporary
               sleep and temporary paralysis, so both conditions
               receive the same alternate message */
            if (!mtmp->mcanmove || !mtmp->data->mmove) {
                pline("%s seems to flinch.", Adjmonnam(mtmp, "immobile"));
            } else if (flees_light(mtmp)) {
                if (rn2(10) || Deaf)
                    pline("%s flees from the painful light of %s.",
                          Monnam(mtmp), bare_artifactname(uwep));
                else
                    verbalize("Bright light!");
            } else
                pline("%s turns to flee.", Monnam(mtmp));
        }
        mtmp->mflee = 1;
    }
    /* ignore recently-stepped spaces when made to flee */
    memset(mtmp->mtrack, 0, sizeof(mtmp->mtrack));
}

STATIC_OVL void
distfleeck(mtmp, inrange, nearby, scared)
register struct monst *mtmp;
int *inrange, *nearby, *scared;
{
    int seescaryx, seescaryy;
    boolean sawscary = FALSE, bravegremlin = (rn2(5) == 0);

    *inrange = (dist2(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy)
                <= (BOLT_LIM * BOLT_LIM));
    *nearby = *inrange && monnear(mtmp, mtmp->mux, mtmp->muy);

    /* Note: if your image is displaced, the monster sees the Elbereth
     * at your displaced position, thus never attacking your displaced
     * position, but possibly attacking you by accident.  If you are
     * invisible, it sees the Elbereth at your real position, thus never
     * running into you by accident but possibly attacking the spot
     * where it guesses you are.
     */
    if (!mtmp->mcansee || (Invis && !SPWQ(mtmp->data, SPW_PERCEIVES, perceives(mtmp->data)))) {
        seescaryx = mtmp->mux;
        seescaryy = mtmp->muy;
    } else {
        seescaryx = u.ux;
        seescaryy = u.uy;
    }

    sawscary = (*nearby || mtmp->isshk || mtmp->ispriest)
        && onscary(seescaryx, seescaryy, mtmp);
    if (*nearby && (sawscary
                    || (flees_light(mtmp) && !bravegremlin)
                    || (!mtmp->mpeaceful && in_your_sanctuary(mtmp, 0, 0)))) {
        *scared = 1;
        monflee(mtmp, rnd(rn2(7) ? 10 : 100), TRUE, TRUE);
    } else
        *scared = 0;
}

#undef flees_light

/* perform a special one-time action for a monster; returns -1 if nothing
   special happened, 0 if monster uses up its turn, 1 if monster is killed */
STATIC_OVL int
m_arrival(mon)
struct monst *mon;
{
    mon->mstrategy &= ~STRAT_ARRIVE; /* always reset */

    return -1;
}

/* returns 1 if monster died moving, 0 otherwise */
/* The whole dochugw/m_move/distfleeck/mfndpos section is serious spaghetti
 * code. --KAA
 */
int
dochug(mtmp)
register struct monst *mtmp;
{
    register struct permonst *mdat;
    register int tmp = 0;
    int inrange, nearby, scared;

    /*  Pre-movement adjustments
     */

    mdat = mtmp->data;

#ifdef NH_MT2_TRACE
    nh_mt2_trace_elig = mt2_eligible(mtmp);
    nh_mt2_trace_rng0 = nle_rng_state(0)->n;
    if (nh_mt2_fast && nh_mt2_trace_elig)
        return dochug_fast(mtmp);
#else
    if (nh_mt2_fast && mt2_eligible(mtmp))
        return dochug_fast(mtmp);
#endif
    nh_mt2_hero_valid = 0; /* the original path may change hero properties (attacks, theft, engulfing): recompute before the next fast move */

    if (mtmp->mstrategy & STRAT_ARRIVE) {
        int res = m_arrival(mtmp);
        if (res >= 0)
            return res;
    }

    /* check for waitmask status change */
    if ((mtmp->mstrategy & STRAT_WAITFORU)
        && (m_canseeu(mtmp) || mtmp->mhp < mtmp->mhpmax))
        mtmp->mstrategy &= ~STRAT_WAITFORU;

    /* update quest status flags */
    quest_stat_check(mtmp);

    if (!mtmp->mcanmove || (mtmp->mstrategy & STRAT_WAITMASK)) {
        if (Hallucination)
            newsym(mtmp->mx, mtmp->my);
        if (mtmp->mcanmove && (mtmp->mstrategy & STRAT_CLOSE)
            && !mtmp->msleeping && monnear(mtmp, u.ux, u.uy))
            quest_talk(mtmp); /* give the leaders a chance to speak */
        return 0;             /* other frozen monsters can't do anything */
    }

    /* there is a chance we will wake it */
    if (mtmp->msleeping && !disturb(mtmp)) {
        if (Hallucination)
            newsym(mtmp->mx, mtmp->my);
        return 0;
    }

    /* not frozen or sleeping: wipe out texts written in the dust */
    wipe_engr_at(mtmp->mx, mtmp->my, 1, FALSE);

    /* confused monsters get unconfused with small probability */
    if (mtmp->mconf && !rn2(50))
        mtmp->mconf = 0;

    /* stunned monsters get un-stunned with larger probability */
    if (mtmp->mstun && !rn2(10))
        mtmp->mstun = 0;

    /* some monsters teleport */
    if (mtmp->mflee && !rn2(40) && SPWQ(mdat, SPW_TPORT, can_teleport(mdat)) && !mtmp->iswiz
        && !level.lflags.noteleport) {
        (void) rloc(mtmp, TRUE);
        return 0;
    }
    if (mdat->msound == MS_SHRIEK && !um_dist(mtmp->mx, mtmp->my, 1))
        m_respond(mtmp);
    if (mdat == &mons[PM_MEDUSA] && couldsee(mtmp->mx, mtmp->my))
        m_respond(mtmp);
    if (DEADMONSTER(mtmp))
        return 1; /* m_respond gaze can kill medusa */

    /* fleeing monsters might regain courage */
    if (mtmp->mflee && !mtmp->mfleetim && mtmp->mhp == mtmp->mhpmax
        && !rn2(25))
        mtmp->mflee = 0;

    /* cease conflict-induced swallow/grab if conflict has ended */
    if (mtmp == u.ustuck && mtmp->mpeaceful && !mtmp->mconf && !Conflict) {
        release_hero(mtmp);
        return 0; /* uses up monster's turn */
    }

    set_apparxy(mtmp);
    /* Must be done after you move and before the monster does.  The
     * set_apparxy() call in m_move() doesn't suffice since the variables
     * inrange, etc. all depend on stuff set by set_apparxy().
     */

    /* Monsters that want to acquire things */
    /* may teleport, so do it before inrange is set */
    if (SPWQ(mdat, SPW_COVETOUS, is_covetous(mdat)))
        (void) tactics(mtmp);

    /* check distance and scariness of attacks */
    distfleeck(mtmp, &inrange, &nearby, &scared);

    if (find_defensive(mtmp)) {
        if (use_defensive(mtmp) != 0)
            return 1;
    } else if (find_misc(mtmp)) {
        if (use_misc(mtmp) != 0)
            return 1;
    }

    /* Demonic Blackmail! */
    if (nearby && mdat->msound == MS_BRIBE && mtmp->mpeaceful && !mtmp->mtame
        && !u.uswallow) {
        if (mtmp->mux != u.ux || mtmp->muy != u.uy) {
            pline("%s whispers at thin air.",
                  cansee(mtmp->mux, mtmp->muy) ? Monnam(mtmp) : "It");

            if (is_demon(youmonst.data)) {
                /* "Good hunting, brother" */
                if (!tele_restrict(mtmp))
                    (void) rloc(mtmp, TRUE);
            } else {
                mtmp->minvis = mtmp->perminvis = 0;
                /* Why?  For the same reason in real demon talk */
                pline("%s gets angry!", Amonnam(mtmp));
                mtmp->mpeaceful = 0;
                set_malign(mtmp);
                /* since no way is an image going to pay it off */
            }
        } else if (demon_talk(mtmp))
            return 1; /* you paid it off */
    }

    /* the watch will look around and see if you are up to no good :-) */
    if (SPWQ(mdat, SPW_WATCH, is_watch(mdat))) {
        watch_on_duty(mtmp);

    } else if (SPWQ(mdat, SPW_MINDFLAYER, is_mind_flayer(mdat)) && !rn2(20)) {
        struct monst *m2, *nmon = (struct monst *) 0;

        if (canseemon(mtmp))
            pline("%s concentrates.", Monnam(mtmp));
        if (distu(mtmp->mx, mtmp->my) > BOLT_LIM * BOLT_LIM) {
            You("sense a faint wave of psychic energy.");
            goto toofar;
        }
        pline("A wave of psychic energy pours over you!");
        if (mtmp->mpeaceful
            && (!Conflict || resist(mtmp, RING_CLASS, 0, 0))) {
            pline("It feels quite soothing.");
        } else if (!u.uinvulnerable) {
            register boolean m_sen = sensemon(mtmp);

            if (m_sen || (Blind_telepat && rn2(2)) || !rn2(10)) {
                int dmg;
                pline("It locks on to your %s!",
                      m_sen ? "telepathy" : Blind_telepat ? "latent telepathy"
                                                          : "mind");
                dmg = rnd(15);
                if (Half_spell_damage)
                    dmg = (dmg + 1) / 2;
                losehp(dmg, "psychic blast", KILLED_BY_AN);
            }
        }
        for (m2 = fmon; m2; m2 = nmon) {
            nmon = m2->nmon;
            if (DEADMONSTER(m2))
                continue;
            if (m2->mpeaceful == mtmp->mpeaceful)
                continue;
            if (SPWQ(m2->data, SPW_MINDLESS, mindless(m2->data)))
                continue;
            if (m2 == mtmp)
                continue;
            if ((telepathic(m2->data) && (rn2(2) || m2->mblinded))
                || !rn2(10)) {
                if (cansee(m2->mx, m2->my))
                    pline("It locks on to %s.", mon_nam(m2));
                m2->mhp -= rnd(15);
                if (DEADMONSTER(m2))
                    monkilled(m2, "", AD_DRIN);
                else
                    m2->msleeping = 0;
            }
        }
    }
 toofar:

    /* If monster is nearby you, and has to wield a weapon, do so.   This
     * costs the monster a move, of course.
     */
    if ((!mtmp->mpeaceful || Conflict) && inrange
        && dist2(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy) <= 8
        && SPWQ(mdat, SPW_WEAPATTK, attacktype(mdat, AT_WEAP))) {
        struct obj *mw_tmp;

        /* The scared check is necessary.  Otherwise a monster that is
         * one square near the player but fleeing into a wall would keep
         * switching between pick-axe and weapon.  If monster is stuck
         * in a trap, prefer ranged weapon (wielding is done in thrwmu).
         * This may cost the monster an attack, but keeps the monster
         * from switching back and forth if carrying both.
         */
        mw_tmp = MON_WEP(mtmp);
        if (!(scared && mw_tmp && is_pick(mw_tmp))
            && mtmp->weapon_check == NEED_WEAPON
            && !(mtmp->mtrapped && !nearby && select_rwep(mtmp))) {
            mtmp->weapon_check = NEED_HTH_WEAPON;
            if (mon_wield_item(mtmp) != 0)
                return 0;
        }
    }

    /*  Now the actual movement phase
     */

    if (!nearby || mtmp->mflee || scared || mtmp->mconf || mtmp->mstun
        || (mtmp->minvis && !rn2(3))
        || (mdat->mlet == S_LEPRECHAUN && !findgold(invent)
            && (findgold(mtmp->minvent) || rn2(2)))
        || (SPWQ(mdat, SPW_WANDER, is_wanderer(mdat)) && !rn2(4)) || (Conflict && !mtmp->iswiz)
        || (!mtmp->mcansee && !rn2(4)) || mtmp->mpeaceful) {
        /* Possibly cast an undirected spell if not attacking you */
        /* note that most of the time castmu() will pick a directed
           spell and do nothing, so the monster moves normally */
        /* arbitrary distance restriction to keep monster far away
           from you from having cast dozens of sticks-to-snakes
           or similar spells by the time you reach it */
        if (dist2(mtmp->mx, mtmp->my, u.ux, u.uy) <= 49
            && !mtmp->mspec_used) {
            struct attack *a;

            for (a = &mdat->mattk[0]; a < &mdat->mattk[NATTK]; a++) {
                if (a->aatyp == AT_MAGC
                    && (a->adtyp == AD_SPEL || a->adtyp == AD_CLRC)) {
                    if (castmu(mtmp, a, FALSE, FALSE)) {
                        tmp = 3;
                        break;
                    }
                }
            }
        }

        tmp = m_move(mtmp, 0);
#ifdef NH_MT2_TRACE
        if (nh_mt2_trace_elig && nh_mt2_trace_fp && mt2_trace_on()) fprintf(nh_mt2_trace_fp, "E%d  after m_move id%u tmp%d rng%d\n", nh_ctx_serial, mtmp->m_id, tmp, nle_rng_state(0)->n);
#endif
        if (tmp != 2)
            distfleeck(mtmp, &inrange, &nearby, &scared); /* recalc */

        switch (tmp) { /* for pets, cases 0 and 3 are equivalent */
        case 0: /* no movement, but it can still attack you */
        case 3: /* absolutely no movement */
            /* vault guard might have vanished */
            if (mtmp->isgd && (DEADMONSTER(mtmp) || mtmp->mx == 0))
                return 1; /* behave as if it died */
            /* During hallucination, monster appearance should
             * still change - even if it doesn't move.
             */
            if (Hallucination)
                newsym(mtmp->mx, mtmp->my);
            break;
        case 1: /* monster moved */
            /* Maybe it stepped on a trap and fell asleep... */
            if (mtmp->msleeping || !mtmp->mcanmove)
                return 0;
            /* Monsters can move and then shoot on same turn;
               our hero can't.  Is that fair? */
            if (!nearby && (SPWQ(mdat, SPW_RANGED, ranged_attk(mdat)) || find_offensive(mtmp)))
                break;
            /* engulfer/grabber checks */
            if (mtmp == u.ustuck) {
                /* a monster that's digesting you can move at the
                 * same time -dlc
                 */
                if (u.uswallow)
                    return mattacku(mtmp);
                /* if confused grabber has wandered off, let go */
                if (distu(mtmp->mx, mtmp->my) > 2)
                    unstuck(mtmp);
            }
            return 0;
        case 2: /* monster died */
            return 1;
        }
    }

    /*  Now, attack the player if possible - one attack set per monst
     */

    if (!mtmp->mpeaceful || (Conflict && !resist(mtmp, RING_CLASS, 0, 0))) {
        if (inrange && !SPWQ(mdat, SPW_NOATTACKS, noattacks(mdat))
            && (Upolyd ? u.mh : u.uhp) > 0 && !scared && tmp != 3)
            if (mattacku(mtmp))
                return 1; /* monster died (e.g. exploded) */

        if (mtmp->wormno)
            wormhitu(mtmp);
    }
    /* special speeches for quest monsters */
    if (!mtmp->msleeping && mtmp->mcanmove && nearby)
        quest_talk(mtmp);
    /* extra emotional attack for vile monsters */
    if (inrange && mtmp->data->msound == MS_CUSS && !mtmp->mpeaceful
        && couldsee(mtmp->mx, mtmp->my) && !mtmp->minvis && !rn2(5))
        cuss(mtmp);

    return (tmp == 2);
}

#ifdef NH_MT2_CG
extern int nh_mt2_cur_elig; extern unsigned long long nh_mt2_c[64];
enum { C_MOVES, C_PLAIN, C_DOORWIN, C_PILEWIN, C_TRAPWIN, C_LIQWIN, C_BARSWIN, C_GASWIN, C_ALTARWIN, C_ORIGDOOR, C_OCCWIN, C_TEMPLE, C_SOKO,
       C_BOXEMPTY, C_SEARCH, C_SEARCHOBJ, C_TARGET, C_MOVED, C_NOMOVE, C_TRACKHIT, C_DESTOBJ, C_DESTTRAP, C_DESTDOOR, C_DESTSEE, C_HIDES,
       C_RANGED, C_REFLECT, C_UPOLYD, C_ENGRHERE, C_ENGRANY, C_REGIONS, C_DISPLACES, C_INTEREST, C_USESITEMS, C_MINVENT, C_APPR0, C_ITEMSPECIES,
       C_SHOPROOM, C_CANOPEN, C_ORIGSEE, C_CNT0, C_CNT1, C_CNT2, C_CNT3, C_CNT4, C_CNT5, C_CNT6, C_CNT7, C_CNT8, C_NODIAG, C_INFRA_SENSE, C_MMOVED3 };
#define MT2C(k) do { if (nh_mt2_cur_elig) nh_mt2_c[k]++; } while (0)
static void mt2_window_stats(struct monst *m) {
    int x = m->mx, y = m->my, nx, ny, door = 0, pile = 0, trap = 0, liq = 0, bars = 0, gas = 0, altar = 0, occ = 0, see = 0;
    for (nx = x - 1; nx <= x + 1; nx++) for (ny = y - 1; ny <= y + 1; ny++) {
        int t; if (!isok(nx, ny) || (nx == x && ny == y)) continue; t = TYP_AT(nx, ny);
        if (IS_DOOR(t)) door = 1; if (t == IRONBARS) bars = 1; if (IS_ALTAR(t)) altar = 1;
        if (t == POOL || t == MOAT || t == WATER || t == LAVAPOOL || t == DRAWBRIDGE_UP || t == DRAWBRIDGE_DOWN) liq = 1;
        if (NH_SUMMARY(nx, ny).move_pile) pile = 1; if (NH_SUMMARY(nx, ny).move_trap_present) trap = 1; if (NH_SUMMARY(nx, ny).move_gas) gas = 1;
        if (MON_AT(nx, ny)) occ = 1; if (cansee(nx, ny)) see = 1;
    }
    MT2C(C_MOVES); if (door) MT2C(C_DOORWIN); if (pile) MT2C(C_PILEWIN); if (trap) MT2C(C_TRAPWIN); if (liq) MT2C(C_LIQWIN); if (bars) MT2C(C_BARSWIN);
    if (gas || NH_SUMMARY(x, y).move_gas) MT2C(C_GASWIN); if (altar) MT2C(C_ALTARWIN); if (IS_DOOR(TYP_AT(x, y))) MT2C(C_ORIGDOOR); if (occ) MT2C(C_OCCWIN);
    if (level.lflags.has_temple) MT2C(C_TEMPLE); if (Sokoban) MT2C(C_SOKO); if (see) MT2C(C_DESTSEE); if (couldsee(x, y)) MT2C(C_ORIGSEE);
    if (!door && !pile && !trap && !liq && !bars && !gas && !altar && !IS_DOOR(TYP_AT(x, y)) && !NH_SUMMARY(x, y).move_gas && !level.lflags.has_temple && !Sokoban) MT2C(C_PLAIN);
    if ((m->data->mflags3 & M3_DISPLACES) || m->data == &mons[PM_PURPLE_WORM]) MT2C(C_DISPLACES);
    if (NODIAG(monsndx(m->data))) MT2C(C_NODIAG);
    { int ex = 0, ox, oy; for (ox = max(1, x - 5); ox <= min(COLNO - 1, x + 5) && !ex; ox++) for (oy = max(0, y - 5); oy <= min(ROWNO - 1, y + 5); oy++) if (NH_SUMMARY(ox, oy).move_obj_present) { ex = 1; break; }
      if (!ex) MT2C(C_BOXEMPTY); }
    if (m->minvent) MT2C(C_MINVENT); if (ranged_attk(m->data)) MT2C(C_RANGED); if (Reflecting) MT2C(C_REFLECT); if (Upolyd) MT2C(C_UPOLYD);
    if (engr_at(x, y)) MT2C(C_ENGRHERE); if (head_engr) MT2C(C_ENGRANY); if (n_regions) MT2C(C_REGIONS); if (hides_under(m->data)) MT2C(C_HIDES);
    if (likes_gold(m->data) || likes_gems(m->data) || likes_objs(m->data) || likes_magic(m->data) || throws_rocks(m->data) || hides_under(m->data)) MT2C(C_ITEMSPECIES);
    if (!(nohands(m->data) || verysmall(m->data))) MT2C(C_CANOPEN);
    if (*in_rooms(x, y, SHOPBASE)) MT2C(C_SHOPROOM);
    if (nh_display_sense & ~NH_SENSE_VALID) MT2C(C_INFRA_SENSE);
}
#else
#define MT2C(k) do { } while (0)
#endif
static NEARDATA const char practical[] = { WEAPON_CLASS, ARMOR_CLASS,
                                           GEM_CLASS, FOOD_CLASS, 0 };
static NEARDATA const char magical[] = { AMULET_CLASS, POTION_CLASS,
                                         SCROLL_CLASS, WAND_CLASS,
                                         RING_CLASS,   SPBOOK_CLASS, 0 };
static NEARDATA const char indigestion[] = { BALL_CLASS, ROCK_CLASS, 0 };
static NEARDATA const char boulder_class[] = { ROCK_CLASS, 0 };
static NEARDATA const char gem_class[] = { GEM_CLASS, 0 };

boolean
itsstuck(mtmp)
register struct monst *mtmp;
{
    if (mtmp == u.ustuck && !u.uswallow && sticks(youmonst.data)) { /* same predicate; the identity test first skips the attack-table walk */
        pline("%s cannot escape from you!", Monnam(mtmp));
        return TRUE;
    }
    return FALSE;
}

/*
 * should_displace()
 *
 * Displacement of another monster is a last resort and only
 * used on approach. If there are better ways to get to target,
 * those should be used instead. This function does that evaluation.
 */
boolean
should_displace(mtmp, poss, info, cnt, gx, gy)
struct monst *mtmp;
coord *poss; /* coord poss[9] */
long *info;  /* long info[9] */
int cnt;
xchar gx, gy;
{
    int shortest_with_displacing = -1;
    int shortest_without_displacing = -1;
    int count_without_displacing = 0;
    register int i, nx, ny;
    int ndist;

    for (i = 0; i < cnt; i++) {
        nx = poss[i].x;
        ny = poss[i].y;
        ndist = dist2(nx, ny, gx, gy);
        if ((info[i] & ALLOW_MDISP) && !(info[i] & ALLOW_M) /* ALLOW_MDISP is only set with a monster there */
            && !undesirable_disp(mtmp, nx, ny)) {
            if (shortest_with_displacing == -1
                || (ndist < shortest_with_displacing))
                shortest_with_displacing = ndist;
        } else {
            int upd = (shortest_without_displacing == -1) | (ndist < shortest_without_displacing);
            int m = -upd;
            shortest_without_displacing = (ndist & m) | (shortest_without_displacing & ~m);
            count_without_displacing++;
        }
    }
    if (shortest_with_displacing > -1
        && (shortest_with_displacing < shortest_without_displacing
            || !count_without_displacing))
        return TRUE;
    return FALSE;
}


/* ===================================================================================================================
 * Monster-turn v2 (mt2): exact fast path for an ordinary hostile monster far from (distmin > 9) and unseen by the hero.
 * mt2_eligible() excludes every monster, species, hero and level state under which any skipped original statement could
 * have an effect; what remains is evaluated in the original order with the original RNG draws. Runtime switch: NH_MT2=0.
 * =================================================================================================================== */
#include <stdlib.h>
int nh_mt2_fast = 1, nh_mt2_s3 = 1, nh_mt2_s7 = 1; /* NH_MT2 (whole fast path), NH_MT2_S3 (box-cell object search), NH_MT2_S7 (door windows) */
static void __attribute__((constructor))
nh_mt2_init(void)
{
    const char *e = getenv("NH_MT2");
    if (e && *e == '0')
        nh_mt2_fast = 0;
    e = getenv("NH_MT2_S3");
    if (e && *e == '0')
        nh_mt2_s3 = 0;
    e = getenv("NH_MT2_S7");
    if (e && *e == '0')
        nh_mt2_s7 = 0;
}
#ifdef NH_MT2_TRACE
#include <stdio.h>
#include "isaac64.h"
extern isaac64_ctx *FDECL(nle_rng_state, (int));
FILE *nh_mt2_trace_fp;
int nh_mt2_trace_elig, nh_mt2_trace_rng0, nh_mt2_trace_env = -2, nh_mt2_trace_env_hi;
static int mt2_trace_on(void) { if (nh_mt2_trace_env == -2) { const char *e = getenv("NH_MT2_TRACE_ENV"); nh_mt2_trace_env = e ? atoi(e) : -1; nh_mt2_trace_env_hi = nh_mt2_trace_env; if (e && strchr(e, ':')) nh_mt2_trace_env_hi = atoi(strchr(e, ':') + 1); } return nh_mt2_trace_env < 0 || (nh_ctx_serial >= nh_mt2_trace_env && nh_ctx_serial <= nh_mt2_trace_env_hi); }
static void
mt2_trace(struct monst *m, int omx, int omy, int gx, int gy, int appr, int cnt, coord *poss, long *info, int chi, int nix, int niy, int mmoved)
{
    int i;
    if (!nh_mt2_trace_fp) {
        const char *p = getenv("NH_MT2_TRACE");
        if (!p || !(nh_mt2_trace_fp = fopen(p, "w"))) return;
    }
    fprintf(nh_mt2_trace_fp, "E%d %ld id%u pm%d e%d %d,%d g%d,%d a%d c%d", nh_ctx_serial, moves, m->m_id, monsndx(m->data), nh_mt2_trace_rng0, omx, omy, gx, gy, appr, cnt);
    for (i = 0; i < cnt; i++) fprintf(nh_mt2_trace_fp, " %d,%d/%lx", poss[i].x, poss[i].y, info[i]);
    fprintf(nh_mt2_trace_fp, " -> %d %d,%d m%d rng%d |", chi, nix, niy, mmoved, nle_rng_state(0)->n);
    { int dx, dy; for (dx = -1; dx <= 1; dx++) for (dy = -1; dy <= 1; dy++) { int x = omx + dx, y = omy + dy; if (!isok(x, y)) continue;
        fprintf(nh_mt2_trace_fp, " %d,%d:t%d/f%d/p%d/T%d/g%d/o%d/m%d", x, y, TYP_AT(x, y), NH_TILE(x, y).rmflags, NH_SUMMARY(x, y).move_pile,
                NH_SUMMARY(x, y).move_trap_present, NH_SUMMARY(x, y).move_gas, NH_SUMMARY(x, y).move_obj_present, MON_AT(x, y) ? 1 : 0); } }
    fputc('\n', nh_mt2_trace_fp);
}
#define MT2_TRACE(...) do { if (nh_mt2_trace_elig && mt2_trace_on()) mt2_trace(__VA_ARGS__); } while (0)
#else
#define MT2_TRACE(...) do { } while (0)
#endif

/* hero-state half of the predicate: recomputed at each movemon() pass and after any monster move that was not a pure fast move
   (only hero actions, old-path monster moves and the fast path's near tail can change these properties) */
static int
mt2_hero_bad(void)
{
    if (!nh_mt2_hero_valid) {
        nh_mt2_hero_bad = (u.uswallow || Underwater || Hallucination || Conflict || Reflecting
                           || u.uundetected || U_AP_TYPE != M_AP_NOTHING); /* Invis/Displaced: set_apparxy(); Upolyd: lined_up() draws */
        nh_mt2_hero_valid = 1;
    }
    return nh_mt2_hero_bad;
}

#ifdef NH_MT2_CG
unsigned long long nh_mt2_why[16], nh_mt2_why_sp[NUMMONS], nh_mt2_why_h[12];
int nh_mt2_last_why;
#define MT2WHY(k) (nh_mt2_why[k]++, nh_mt2_last_why = (k), 0)
#define MT2WHY_SP(i) (nh_mt2_why_sp[i]++)
#define MT2WHY_H() do { nh_mt2_why_h[0] += !!u.uswallow; nh_mt2_why_h[1] += !!Underwater; nh_mt2_why_h[2] += !!Invis; nh_mt2_why_h[3] += !!Displaced; \
    nh_mt2_why_h[4] += !!Hallucination; nh_mt2_why_h[5] += !!Conflict; nh_mt2_why_h[6] += !!Upolyd; nh_mt2_why_h[7] += !!Reflecting; \
    nh_mt2_why_h[8] += !!u.uundetected; nh_mt2_why_h[9] += (U_AP_TYPE != M_AP_NOTHING); } while (0)
#else
#define MT2WHY_SP(i) ((void) 0)
#define MT2WHY_H() ((void) 0)
#define MT2WHY(k) 0
#endif
/* v1.8: the per-monster status part of the predicate as masked 64-bit word compares. The masks are calibrated once by
   probing each field on a zeroed struct monst (set the field, record the bytes it occupies), so no layout is assumed; a
   field that must be zero contributes its bits to the mask only, a field that must be all-ones (mcansee, mcanmove,
   cham == NON_PM) to the mask and the wanted value. Pure, so the test order is irrelevant. */
struct nh_mt2_ew { int n; unsigned off[8]; unsigned long long mask[8], want[8]; };
static struct nh_mt2_ew nh_mt2_ew;
static int nh_mt2_ew_ready;
static pthread_once_t nh_mt2_ew_once = PTHREAD_ONCE_INIT;
static void
nh_mt2_ew_probe(unsigned char *mb, unsigned char *wb, const struct monst *m, int want_ones)
{
    const unsigned char *b = (const unsigned char *) m;
    size_t i;
    for (i = 0; i < sizeof *m; i++)
        if (b[i]) { mb[i] |= b[i]; if (want_ones) wb[i] |= b[i]; }
}
#define NH_EW_ZERO(f) do { memset(&pm, 0, sizeof pm); pm.f = ~0; nh_mt2_ew_probe(mb, wb, &pm, 0); } while (0)
#define NH_EW_ONES(f) do { memset(&pm, 0, sizeof pm); pm.f = ~0; nh_mt2_ew_probe(mb, wb, &pm, 1); } while (0)
static void
nh_mt2_ew_init(void)
{
    struct monst pm;
    unsigned char mb[sizeof(struct monst)], wb[sizeof(struct monst)];
    size_t off;
    memset(mb, 0, sizeof mb); memset(wb, 0, sizeof wb);
    NH_EW_ZERO(mtame); NH_EW_ZERO(m_ap_type); NH_EW_ZERO(mundetected); NH_EW_ZERO(mflee); NH_EW_ZERO(msleeping);
    NH_EW_ZERO(mstun); NH_EW_ZERO(mconf); NH_EW_ZERO(mtrapped); NH_EW_ZERO(isshk); NH_EW_ZERO(isgd); NH_EW_ZERO(ispriest);
    NH_EW_ZERO(iswiz); NH_EW_ZERO(wormno); NH_EW_ZERO(mstrategy); NH_EW_ZERO(meating);
    NH_EW_ONES(mcansee); NH_EW_ONES(mcanmove); NH_EW_ONES(cham); /* NON_PM == -1: all ones */
    nh_mt2_ew.n = 0;
    for (off = 0; off + 8 <= sizeof(struct monst); off += 8) {
        unsigned long long mk = 0, wt = 0;
        int k;
        for (k = 7; k >= 0; k--) { mk = (mk << 8) | mb[off + k]; wt = (wt << 8) | wb[off + k]; }
        if (mk) {
            if (nh_mt2_ew.n == 8) panic("nh_mt2_ew_init: too many words");
            nh_mt2_ew.off[nh_mt2_ew.n] = (unsigned) off; nh_mt2_ew.mask[nh_mt2_ew.n] = mk; nh_mt2_ew.want[nh_mt2_ew.n] = wt;
            nh_mt2_ew.n++;
        }
    }
    __atomic_store_n(&nh_mt2_ew_ready, 1, __ATOMIC_RELEASE);
}
static inline int
mt2_status_ok(const struct monst *m)
{
    const unsigned char *b = (const unsigned char *) m;
    int i;
    if (!__atomic_load_n(&nh_mt2_ew_ready, __ATOMIC_ACQUIRE)) pthread_once(&nh_mt2_ew_once, nh_mt2_ew_init);
    for (i = 0; i < nh_mt2_ew.n; i++) {
        unsigned long long w;
        memcpy(&w, b + nh_mt2_ew.off[i], 8);
        if ((w & nh_mt2_ew.mask[i]) != nh_mt2_ew.want[i]) return 0;
    }
    return 1;
}
static int
mt2_eligible_fast(struct monst *m)
{
    if (!mt2_status_ok(m) || m == u.ustuck) return 0;
    if (nh_spw[m->data - mons] & SPW_MT2_NOFAST) return 0;
    if (mt2_hero_bad()) return 0;
    {
        int ddx = abs(m->mx - u.ux), ddy = abs(m->my - u.uy);
        if ((ddx > ddy ? ddx : ddy) <= 1) return 0;
    }
    return 1;
}
#ifdef NH_MT2_CG
static int mt2_eligible_slow(struct monst *m);
int
mt2_eligible(m)
struct monst *m;
{
    int slow = mt2_eligible_slow(m), fast = mt2_eligible_fast(m); /* census build: the original chain stays the authority */
    if (slow != fast) fprintf(stderr, "MT2_ELIG_MISMATCH id%u slow %d fast %d\n", m->m_id, slow, fast);
    return slow;
}
static int
mt2_eligible_slow(struct monst *m)
#else
int
mt2_eligible(m)
struct monst *m;
{
    return mt2_eligible_fast(m);
}
static int
mt2_eligible_slow(struct monst *m) __attribute__((unused));
static int
mt2_eligible_slow(struct monst *m)
#endif
{
    const struct permonst *p = m->data;

    if (m->mtame) return MT2WHY(0);
    if (m->isshk || m->ispriest || m->isgd || m->iswiz || m->wormno) return MT2WHY(2);
    if (m->mstrategy) return MT2WHY(3);
    if (m->msleeping) return MT2WHY(4);
    if (m->mflee) return MT2WHY(5);
    if (m->mconf || m->mstun || m->mtrapped || m->meating || !m->mcanmove || !m->mcansee
        || m->mundetected || M_AP_TYPE(m) != M_AP_NOTHING || m->cham != NON_PM || m == u.ustuck)
        return MT2WHY(6);
    if (nh_spw[p - mons] & SPW_MT2_NOFAST) {
        MT2WHY_SP(p - mons);
        return MT2WHY(7);
    }
    if (mt2_hero_bad()) {
        MT2WHY_H();
        return MT2WHY(8);
    }
    {
        int ddx = abs(m->mx - u.ux), ddy = abs(m->my - u.uy);
        if ((ddx > ddy ? ddx : ddy) <= 1) /* adjacent (nearby): the melee path stays original */
            return MT2WHY(9);
    }
    return 1;
}

/* linedup()'s pure geometric pre-tests: FALSE means lined_up() sets tbx/tby and returns FALSE without any draw */
static inline int
nh_lined_geom(const struct monst *m)
{
    int dx = m->mux - m->mx, dy = m->muy - m->my, ax = abs(dx), ay = abs(dy);
    return (dx || dy) && (!dx || !dy || ax == ay) && (ax > ay ? ax : ay) < BOLT_LIM;
}

/* *in_rooms(x, y, SHOPBASE) != '\0' */
static inline int
mt2_in_shop(int x, int y)
{
    int rno = NH_TILE(x, y).roomno;
    if (rno == NO_ROOM) return 0;
    if (rno >= ROOMOFFSET) return rooms[rno - ROOMOFFSET].rtype >= SHOPBASE;
    return *in_rooms(x, y, SHOPBASE) != '\0';
}

/* any floor object inside the search box: the search loop body has no effect when it never runs */
static inline int
mt2_box_has_objects(int lx, int hx, int ly, int hy)
{
    unsigned int rows = (2U << hy) - (1U << ly), acc = 0;
    int x;
    for (x = lx; x <= hx; x++) acc |= level.move_columns[x + 1].obj;
    return (acc & rows) != 0;
}

#ifndef SQSRCHRADIUS
#define SQSRCHRADIUS 5
#endif
static int
m_move_fast(mtmp)
register struct monst *mtmp;
{
    struct permonst *ptr = mtmp->data;
    unsigned long long spw = nh_spw[ptr - mons];
    register int appr;
    xchar gx, gy, nix, niy, chcnt = 0;
    int chi, cnt;
    boolean likegold = 0, likegems = 0, likeobjs = 0, likemagic = 0, conceals = 0;
    boolean likerock = 0, can_tunnel = 0;
    boolean can_open = 0, can_unlock = 0, doorbuster = 0;
    boolean uses_items = 0, setlikes = 0;
    boolean plain;
    struct monst *mtoo;
    schar mmoved = 0;
    long info[9];
    long flag;
    int omx = mtmp->mx, omy = mtmp->my;
    struct nh_move_column *cols = &level.move_columns[omx];
    coord poss[9];
    unsigned char cbit[9]; /* neighbourhood bit of each candidate: the track test needs no coordinate arithmetic */
    unsigned int door_n, origin_door;
    boolean unlock_known = 0; /* can_unlock is three inventory walks: computed only when a locked door is in reach */
    boolean should_see;

    /* mtrapped and meating are excluded; sawmon (vampshifter) is excluded */
    if ((spw & SPW_HIDESUNDER) && NH_SUMMARY(omx, omy).move_obj_present && rn2(10))
        return 0; /* do not leave hiding place */

    set_apparxy(mtmp); /* second call of the original: re-guesses for Invis/Displaced */
    can_open = !(spw & (SPW_NOHANDS | SPW_VERYSMALL));
    doorbuster = (spw & SPW_GIANT) != 0;
    /* can_unlock (three inventory walks) is only read with a door in reach: computed on the fallback path */

    gx = mtmp->mux;
    gy = mtmp->muy;
    appr = mtmp->mflee ? -1 : 1; /* mflee/mconf were 0 at the eligibility test but distfleeck()/item use in this dochug may set them */
    should_see = (couldsee(omx, omy)
                  && (NH_TILE(gx, gy).lit || !NH_TILE(omx, omy).lit)
                  && (dist2(omx, omy, gx, gy) <= 36));
    if (mtmp->mconf || (u.uswallow && mtmp == u.ustuck)) {
        appr = 0;
    } else {
        /* the original OR chain minus its excluded terms (!mcansee, disguise, uundetected), same evaluation order and draws */
        if ((should_see && Invis && !(spw & SPW_PERCEIVES) && rn2(11))
            || mtmp->mpeaceful
            || ((spw & SPW_RANDAPPR) && !rn2(3)))
            appr = 0;
    }
    if (!(mtmp->mconf || (u.uswallow && mtmp == u.ustuck))) { /* the original's else branch continues */
        if ((spw & SPW_LEPRECHAUN) && (appr == 1)) {
            struct obj *lepgold, *ygold;
            if ((lepgold = findgold(mtmp->minvent))
                && (lepgold->quan > ((ygold = findgold(invent)) ? ygold->quan : 0L)))
                appr = -1;
        }
        if (!should_see && ((uwep && uwep->oartifact == ART_EXCALIBUR) || (spw & SPW_HASEYES)) && nh_track_near[omx + 1][omy + 1]) {
            register coord *cp = gettrack(omx, omy);
            if (cp) {
                gx = cp->x;
                gy = cp->y;
            }
        }
    }

    if ((!mtmp->mpeaceful || !rn2(10)) && !Is_rogue_level(&u.uz)) { /* the draw precedes the level test in the original */
        boolean in_line = FALSE;
        /* v1.8: in_line is only read when appr == 1. Otherwise lined_up() is still called when it could draw (Upolyd) or
           reach linedup()'s path tests (geometrically lined up within BOLT_LIM); in the remaining case its only effect is
           tbx/tby, set here exactly as linedup() sets them before returning FALSE. */
        if (appr == 1 || Upolyd || nh_lined_geom(mtmp)) {
            in_line = (lined_up(mtmp)
                   && (distmin(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy)
                       <= (throws_rocks(youmonst.data) ? 20 : ACURRSTR / 2 + 1)));
        } else {
            tbx = mtmp->mux - mtmp->mx;
            tby = mtmp->muy - mtmp->my;
        }
        if (appr != 1 || !in_line) {
            register int pctload = 0;
            if ((spw & (SPW_LIKEGOLD | SPW_LIKEGEMS | SPW_LIKEOBJS | SPW_LIKEMAGIC | SPW_THROWSROCKS))
                || !(spw & (SPW_MINDLESS | SPW_ANIMAL)))
                pctload = (curr_mon_load(mtmp) * 100) / nh_spw_maxload[ptr - mons];
            likegold = ((spw & SPW_LIKEGOLD) && pctload < 95);
            likegems = ((spw & SPW_LIKEGEMS) && pctload < 85);
            uses_items = (!(spw & (SPW_MINDLESS | SPW_ANIMAL)) && pctload < 75);
            likeobjs = ((spw & SPW_LIKEOBJS) && pctload < 75);
            likemagic = ((spw & SPW_LIKEMAGIC) && pctload < 85);
            likerock = ((spw & SPW_THROWSROCKS) && pctload < 50 && !Sokoban);
            conceals = (spw & SPW_HIDESUNDER) != 0;
            setlikes = TRUE;
        }
    }

    {
        register int minr = SQSRCHRADIUS; /* not too far away */
        register struct obj *otmp;
        register int xx, yy;
        int oomx, oomy, lmx, lmy;
        struct nh_fobj_cursor cursor;

        /* cut down the search radius if it thinks character is closer. */
        if (distmin(mtmp->mux, mtmp->muy, omx, omy) < SQSRCHRADIUS
            && !mtmp->mpeaceful)
            minr--;
        /* guards shouldn't get too distracted */
        if (!mtmp->mpeaceful && SPWQ(ptr, SPW_MERC, is_mercenary(ptr)))
            minr = 1;

        if ((likegold || likegems || likeobjs || likemagic || likerock
             || conceals) && (!mt2_in_shop(omx, omy)
                              || (!rn2(25) && !mtmp->isshk))) {
 look_for_obj:
            MT2C(C_SEARCH);
            oomx = min(COLNO - 1, omx + minr);
            oomy = min(ROWNO - 1, omy + minr);
            lmx = max(1, omx - minr);
            lmy = max(0, omy - minr);
            {
            struct obj *mt2_list[MT2_MAXOBJ];
            int mt2_n = nh_mt2_s3 ? mt2_box_objects(lmx, oomx, lmy, oomy, mt2_list) : -1, mt2_i;
            if (mt2_n < 0) {
            for (otmp = nh_fobj_next(&cursor, (struct obj *) 0, lmx, oomx, lmy, oomy);
                 otmp;
                 otmp = nh_fobj_next(&cursor, otmp, lmx, oomx, lmy, oomy)) {
                /* monsters may pick rocks up, but won't go out of their way
                   to grab them; this might hamper sling wielders, but it cuts
                   down on move overhead by filtering out most common item */
                MT2C(C_SEARCHOBJ);
                if (otmp->otyp == ROCK)
                    continue;
                xx = otmp->ox;
                yy = otmp->oy;
                /* Nymphs take everything.  Most other creatures should not
                 * pick up corpses except as a special case like in
                 * searches_for_item().  We need to do this check in
                 * mpickstuff() as well.
                 */
                if (xx >= lmx && xx <= oomx && yy >= lmy && yy <= oomy) {
                    /* don't get stuck circling around object that's
                       underneath an immobile or hidden monster;
                       paralysis victims excluded */
                    if ((mtoo = m_at(xx, yy)) != 0
                        && (mtoo->msleeping || mtoo->mundetected
                            || (mtoo->mappearance && !mtoo->iswiz)
                            || !mtoo->data->mmove))
                        continue;
                    /* the mfndpos() test for whether to allow a move to a
                       water location accepts flyers, but they can't reach
                       underwater objects, so being able to move to a spot
                       is insufficient for deciding whether to do so */
                    if ((is_pool(xx, yy) && !SPWQ(ptr, SPW_SWIMMER, is_swimmer(ptr)))
                        || (is_lava(xx, yy) && !SPWQ(ptr, SPW_LIKELAVA, likes_lava(ptr))))
                        continue;

                    if (((likegold && otmp->oclass == COIN_CLASS)
                         || (likeobjs && index(practical, otmp->oclass)
                             && (otmp->otyp != CORPSE
                                 || (ptr->mlet == S_NYMPH
                                     && !is_rider(&mons[otmp->corpsenm]))))
                         || (likemagic && index(magical, otmp->oclass))
                         || (uses_items && searches_for_item(mtmp, otmp))
                         || (likerock && otmp->otyp == BOULDER)
                         || (likegems && otmp->oclass == GEM_CLASS
                             && objects[otmp->otyp].oc_material != MINERAL)
                         || (conceals && !cansee(otmp->ox, otmp->oy))
                         || (ptr == &mons[PM_GELATINOUS_CUBE]
                             && !index(indigestion, otmp->oclass)
                             && !(otmp->otyp == CORPSE
                                  && touch_petrifies(&mons[otmp->corpsenm]))))
                        && touch_artifact(otmp, mtmp)) {
                        if (can_carry(mtmp, otmp) > 0
                            && (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)) || !sobj_at(BOULDER, xx, yy))
                            && (!SPWQ(ptr, SPW_UNICORN, is_unicorn(ptr))
                                || objects[otmp->otyp].oc_material == GEMSTONE)
                            /* Don't get stuck circling an Elbereth */
                            && !onscary(xx, yy, mtmp)) {
                            minr = distmin(omx, omy, xx, yy);
                            oomx = min(COLNO - 1, omx + minr);
                            oomy = min(ROWNO - 1, omy + minr);
                            lmx = max(1, omx - minr);
                            lmy = max(0, omy - minr);
                            gx = otmp->ox;
                            gy = otmp->oy;
                            MT2C(C_TARGET);
                            if (gx == omx && gy == omy) {
                                mmoved = 3; /* actually unnecessary */
                                goto postmov;
                            }
                        }
                    }
                }
            }
            } else for (mt2_i = 0; mt2_i < mt2_n; mt2_i++) {
                otmp = mt2_list[mt2_i];
            {
                /* monsters may pick rocks up, but won't go out of their way
                   to grab them; this might hamper sling wielders, but it cuts
                   down on move overhead by filtering out most common item */
                MT2C(C_SEARCHOBJ);
                if (otmp->otyp == ROCK)
                    continue;
                xx = otmp->ox;
                yy = otmp->oy;
                /* Nymphs take everything.  Most other creatures should not
                 * pick up corpses except as a special case like in
                 * searches_for_item().  We need to do this check in
                 * mpickstuff() as well.
                 */
                if (xx >= lmx && xx <= oomx && yy >= lmy && yy <= oomy) {
                    /* don't get stuck circling around object that's
                       underneath an immobile or hidden monster;
                       paralysis victims excluded */
                    if ((mtoo = m_at(xx, yy)) != 0
                        && (mtoo->msleeping || mtoo->mundetected
                            || (mtoo->mappearance && !mtoo->iswiz)
                            || !mtoo->data->mmove))
                        continue;
                    /* the mfndpos() test for whether to allow a move to a
                       water location accepts flyers, but they can't reach
                       underwater objects, so being able to move to a spot
                       is insufficient for deciding whether to do so */
                    if ((is_pool(xx, yy) && !SPWQ(ptr, SPW_SWIMMER, is_swimmer(ptr)))
                        || (is_lava(xx, yy) && !SPWQ(ptr, SPW_LIKELAVA, likes_lava(ptr))))
                        continue;

                    if (((likegold && otmp->oclass == COIN_CLASS)
                         || (likeobjs && index(practical, otmp->oclass)
                             && (otmp->otyp != CORPSE
                                 || (ptr->mlet == S_NYMPH
                                     && !is_rider(&mons[otmp->corpsenm]))))
                         || (likemagic && index(magical, otmp->oclass))
                         || (uses_items && searches_for_item(mtmp, otmp))
                         || (likerock && otmp->otyp == BOULDER)
                         || (likegems && otmp->oclass == GEM_CLASS
                             && objects[otmp->otyp].oc_material != MINERAL)
                         || (conceals && !cansee(otmp->ox, otmp->oy))
                         || (ptr == &mons[PM_GELATINOUS_CUBE]
                             && !index(indigestion, otmp->oclass)
                             && !(otmp->otyp == CORPSE
                                  && touch_petrifies(&mons[otmp->corpsenm]))))
                        && touch_artifact(otmp, mtmp)) {
                        if (can_carry(mtmp, otmp) > 0
                            && (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)) || !sobj_at(BOULDER, xx, yy))
                            && (!SPWQ(ptr, SPW_UNICORN, is_unicorn(ptr))
                                || objects[otmp->otyp].oc_material == GEMSTONE)
                            /* Don't get stuck circling an Elbereth */
                            && !onscary(xx, yy, mtmp)) {
                            minr = distmin(omx, omy, xx, yy);
                            oomx = min(COLNO - 1, omx + minr);
                            oomy = min(ROWNO - 1, omy + minr);
                            lmx = max(1, omx - minr);
                            lmy = max(0, omy - minr);
                            gx = otmp->ox;
                            gy = otmp->oy;
                            MT2C(C_TARGET);
                            if (gx == omx && gy == omy) {
                                mmoved = 3; /* actually unnecessary */
                                goto postmov;
                            }
                        }
                    }
                }
            }
            }
            }
        } else if (likegold) {
            /* don't try to pick up anything else, but use the same loop */
            uses_items = 0;
            likegems = likeobjs = likemagic = likerock = conceals = 0;
            goto look_for_obj;
        }

        if (minr < SQSRCHRADIUS && appr == -1) {
            if (distmin(omx, omy, mtmp->mux, mtmp->muy) <= 3) {
                gx = mtmp->mux;
                gy = mtmp->muy;
            } else
                appr = 1;
        }
    }

    /* can_tunnel: excluded */
    nix = omx;
    niy = omy;
    {
        /* doors are the one special terrain handled here (their rules below); a door cell keeps its pile/trap/gas bits (a scare scroll
           in a doorway must still reach the fallback); any other special cell, origin gas or temple → fallback */
        unsigned int dmask = nh_mt2_s7 ? ~0U : 0U;
        unsigned int bad = nh_move_neighbours((cols[0].special & ~(cols[0].door & dmask)) | cols[0].pile | cols[0].trap | cols[0].gas,
                                              (cols[1].special & ~(cols[1].door & dmask)) | cols[1].pile | cols[1].trap | cols[1].gas,
                                              (cols[2].special & ~(cols[2].door & dmask)) | cols[2].pile | cols[2].trap | cols[2].gas, omy);
        door_n = nh_move_neighbours(cols[0].door & dmask, cols[1].door & dmask, cols[2].door & dmask, omy);
        origin_door = ((cols[1].door & dmask) >> omy) & 1U;
        plain = !bad && !((((cols[1].special & ~(cols[1].door & dmask)) | cols[1].gas) >> omy) & 1U) && !level.lflags.has_temple && !Sokoban
                && distmin(omx, omy, u.ux, u.uy) > 1 && distmin(omx, omy, mtmp->mux, mtmp->muy) > 1;
    }
    if (plain) {
        /* mfndpos() for a window of plain floor: every per-cell test of the original is decided by the masks */
        unsigned int nonrock_n = nh_move_neighbours(cols[0].nonrock, cols[1].nonrock, cols[2].nonrock, omy);
        unsigned int occ = nh_move_neighbours(cols[0].occupied, cols[1].occupied, cols[2].occupied, omy);
        unsigned int cand = nonrock_n & ~occ;
        if (cand & door_n) {
            /* mfndpos(): a closed door needs OPENDOOR, a locked one UNLOCKDOOR, unless amorphous (can_fog excluded) or a doorbuster */
            unsigned int dbits = cand & door_n;
            if (!(spw & SPW_AMORPHOUS) && !doorbuster) {
                while (dbits) {
                    int b = __builtin_ctz(dbits), dm;
                    dbits &= dbits - 1;
                    dm = NH_TILE(omx - 1 + b / 3, omy - 1 + b % 3).rmflags;
                    if (dm & D_LOCKED) {
                        if (!unlock_known) { can_unlock = (can_open && monhaskey(mtmp, TRUE)); unlock_known = 1; }
                        if (!can_unlock) { cand &= ~(1U << b); continue; }
                    }
                    if ((dm & D_CLOSED) && !can_open)
                        cand &= ~(1U << b);
                }
            }
        }
        if (spw & SPW_NODIAG) {
            cand &= 0x0aaU;
        } else if ((cand & 0x145U) && (origin_door || (cand & door_n & 0x145U))) {
            /* mfndpos(): no diagonal move out of or into a door that is not broken away (or any door on the Rogue level) */
            unsigned int dbits = cand & 0x145U;
            boolean rogue = Is_rogue_level(&u.uz);
            int odm = origin_door ? (NH_TILE(omx, omy).rmflags & ~D_BROKEN) : 0;
            while (dbits) {
                int b = __builtin_ctz(dbits), isdoor = (door_n >> b) & 1U;
                dbits &= dbits - 1;
                if (odm || (isdoor && (NH_TILE(omx - 1 + b / 3, omy - 1 + b % 3).rmflags & ~D_BROKEN)) || ((origin_door || isdoor) && rogue))
                    cand &= ~(1U << b);
            }
        }
        if (spw & SPW_NODIAG) {
            ;
        } else if (cand & 0x145U) {
            unsigned int r1 = !((nonrock_n >> 1) & 1U), r3 = !((nonrock_n >> 3) & 1U), r5 = !((nonrock_n >> 5) & 1U), r7 = !((nonrock_n >> 7) & 1U);
            unsigned int squeeze_n = (r1 & r3) | ((r1 & r5) << 2) | ((r7 & r3) << 6) | ((r7 & r5) << 8);
            unsigned int o1 = (occ >> 1) & 1U, o3 = (occ >> 3) & 1U, o5 = (occ >> 5) & 1U, o7 = (occ >> 7) & 1U;
            unsigned int worm_n = (o1 & o3) | ((o1 & o5) << 2) | ((o7 & o3) << 6) | ((o7 & o5) << 8);
            if ((cand & squeeze_n) && cant_squeeze_thru(mtmp))
                cand &= ~squeeze_n;
            worm_n &= cand;
            while (worm_n) {
                int b = __builtin_ctz(worm_n);
                worm_n &= worm_n - 1;
                if (worm_cross(omx, omy, omx - 1 + b / 3, omy - 1 + b % 3))
                    cand &= ~(1U << b);
            }
        }
        cnt = 0;
        while (cand) {
            int b = __builtin_ctz(cand);
            cand &= cand - 1;
            poss[cnt].x = omx - 1 + b / 3;
            poss[cnt].y = omy - 1 + b % 3;
            cbit[cnt] = b;
            info[cnt] = 0L; /* no hero/image/monster cell in a plain window: only NOTONL could be set, and it is read by unicorns alone */
#ifdef NH_MT2_TRACE
            { int dx = poss[cnt].x - u.ux, dy = poss[cnt].y - u.uy; int monseeu = mtmp->mcansee && (!Invis || (spw & SPW_PERCEIVES)); info[cnt] = (monseeu && (!dx || !dy || dx == dy || dx == -dy)) ? NOTONL : 0L; }
#endif
            cnt++;
        }
        flag = ALLOW_U;
    } else {
        can_unlock = (can_open && monhaskey(mtmp, TRUE));
        unlock_known = 1;
        flag = mtmp->mpeaceful ? (ALLOW_SANCT | ALLOW_SSM) : ALLOW_U; /* Conflict is excluded */
        if (spw & SPW_MINION)
            flag |= ALLOW_SANCT;
        if (spw & SPW_PASSBARS)
            flag |= ALLOW_BARS;
        if ((spw & SPW_HUMAN) || ptr == &mons[PM_MINOTAUR])
            flag |= ALLOW_SSM;
        if ((spw & SPW_UNDEAD) && ptr->mlet != S_GHOST)
            flag |= NOGARLIC;
        if (spw & SPW_THROWSROCKS)
            flag |= ALLOW_ROCK;
        if (can_open)
            flag |= OPENDOOR;
        if (can_unlock)
            flag |= UNLOCKDOOR;
        if (doorbuster)
            flag |= BUSTDOOR;
        cnt = mfndpos(mtmp, poss, info, flag);
        for (chi = 0; chi < cnt; chi++)
            cbit[chi] = 3 * (poss[chi].x - omx + 1) + (poss[chi].y - omy + 1);
    }
    {
        register int i, j, nx, ny, nearer;
        unsigned int trackmask;
        int jcnt;
        int ndist, nidist;
        register coord *mtrk;

        chcnt = 0;
        jcnt = min(MTSZ, cnt - 1);
        trackmask = 0;
        for (j = 0; j < jcnt; j++)
            trackmask |= nh_move_position_bit(omx, omy, mtmp->mtrack[j].x, mtmp->mtrack[j].y);
        chi = -1;
        nidist = dist2(nix, niy, gx, gy);
        if (!mtmp->mpeaceful && level.lflags.shortsighted
            && nidist > (couldsee(nix, niy) ? 144 : 36) && appr == 1)
            appr = 0;
        /* avoid (unicorn) and should_displace (ALLOW_MDISP) cannot apply to this population */
        for (i = 0; i < cnt; i++) {
            nx = poss[i].x;
            ny = poss[i].y;
            if (appr != 0 && (trackmask & (1U << cbit[i]))) {
                unsigned int hits = 0;
                mtrk = &mtmp->mtrack[0];
                for (j = 0; j < MTSZ; j++)
                    hits |= (unsigned int) ((j < jcnt) & (nx == mtrk[j].x) & (ny == mtrk[j].y)) << j;
                while (hits) {
                    j = __builtin_ctz(hits);
                    hits &= hits - 1;
                    if (rn2(4 * (cnt - j)))
                        goto nxti;
                }
            }
            ndist = dist2(nx, ny, gx, gy);
            nearer = (ndist < nidist);
            {
                int take = appr ? ((nearer != (appr < 0)) | !mmoved) : (!rn2(++chcnt) | !mmoved);
                int m = -take;
                nix = (xchar) ((nx & m) | (nix & ~m));
                niy = (xchar) ((ny & m) | (niy & ~m));
                nidist = (ndist & m) | (nidist & ~m);
                chi = (i & m) | (chi & ~m);
                mmoved |= (schar) take;
            }
 nxti:
            ;
        }
    }
    MT2_TRACE(mtmp, omx, omy, gx, gy, appr, cnt, poss, info, chi, nix, niy, mmoved);

    if (mmoved) {
        register int j;
        /* itsstuck(): not u.ustuck; m_digweapon_check(): no tunneller */
        if (info[chi] & ALLOW_U) {
            nix = mtmp->mux;
            niy = mtmp->muy;
        }
        if (nix == u.ux && niy == u.uy) {
            mtmp->mux = u.ux;
            mtmp->muy = u.uy;
            return 0;
        }
        /* The monster may attack another based on 1 of 2 conditions:
         * 1 - It may be confused.
         * 2 - It may mistake the monster for your (displaced) image.
         * Pets get taken care of above and shouldn't reach this code.
         * Conflict gets handled even farther away (movemon()).
         */
        if ((info[chi] & ALLOW_M) || (nix == mtmp->mux && niy == mtmp->muy)) {
            struct monst *mtmp2;
            int mstatus;

            mtmp2 = m_at(nix, niy);

            notonhead = mtmp2 && (nix != mtmp2->mx || niy != mtmp2->my);
            /* note: mstatus returns 0 if mtmp2 is nonexistent */
            mstatus = mattackm(mtmp, mtmp2);

            if (mstatus & MM_AGR_DIED) /* aggressor died */
                return 2;

            if ((mstatus & MM_HIT) && !(mstatus & MM_DEF_DIED) && rn2(4)
                && mtmp2->movement >= NORMAL_SPEED) {
                mtmp2->movement -= NORMAL_SPEED;
                notonhead = 0;
                mstatus = mattackm(mtmp2, mtmp); /* return attack */
                if (mstatus & MM_DEF_DIED)
                    return 2;
            }
            return 3;
        }

        if ((info[chi] & ALLOW_MDISP)) {
            struct monst *mtmp2;
            int mstatus;

            mtmp2 = m_at(nix, niy);
            mstatus = mdisplacem(mtmp, mtmp2, FALSE);
            if ((mstatus & MM_AGR_DIED) || (mstatus & MM_DEF_DIED))
                return 2;
            if (mstatus & MM_HIT)
                return 1;
            return 3;
        }

        if (n_regions && !m_in_out_region(mtmp, nix, niy))
            return 3;
        remove_monster(omx, omy);
        mtmp->mx = nix, mtmp->my = niy; /* place_monster() without its consistency diagnostics */
        NH_SET_MON(nix, niy, mtmp);
        mtmp->mstate &= ~(MON_OFFMAP | MON_MIGRATING | MON_LIMBO | MON_BUBBLEMOVE | MON_ENDGAME_FREE | MON_ENDGAME_MIGR);
        for (j = MTSZ - 1; j > 0; j--)
            mtmp->mtrack[j] = mtmp->mtrack[j - 1];
        mtmp->mtrack[0].x = omx;
        mtmp->mtrack[0].y = omy;
    }
    /* !mmoved: unicorn teleport and worms are excluded */
 postmov:
    if (mmoved == 1 || mmoved == 3) {
        boolean canseeit = cansee(mtmp->mx, mtmp->my);

        if (mmoved == 1) {
            nix = mtmp->mx, niy = mtmp->my;
            /* vampshifter door shift: excluded */
            nh_newsym_moved_far(omx, omy); /* update the old position */
            if (NH_SUMMARY(mtmp->mx, mtmp->my).move_trap_present) { /* mintrap() without a trap only clears mtrapped (already 0) */
                if (mintrap(mtmp) >= 2) {
                    if (mtmp->mx)
                        newsym(mtmp->mx, mtmp->my);
                    return 2; /* it died */
                }
                ptr = mtmp->data; /* in case mintrap() caused polymorph */
            }

            if (!unlock_known && IS_DOOR(TYP_AT(mtmp->mx, mtmp->my))) { can_unlock = (can_open && monhaskey(mtmp, TRUE)); unlock_known = 1; }
            /* open a door, or crash through it, if 'mtmp' can */
            if (IS_DOOR(TYP_AT(mtmp->mx, mtmp->my))
                && !SPWQ(ptr, SPW_PASSWALL, passes_walls(ptr)) /* doesn't need to open doors */
                && !can_tunnel) {     /* taken care of below */
                struct rm *here = &NH_TILE(mtmp->mx, mtmp->my);
                boolean btrapped = (here->doormask & D_TRAPPED) != 0,
                        observeit = canseeit && canspotmon(mtmp);

                /* if mon has MKoT, disarm door trap; no message given */
                if (btrapped && has_magic_key(mtmp)) {
                    /* BUG: this lets a vampire or blob or a doorbuster
                       holding the Key disarm the trap even though it isn't
                       using that Key when squeezing under or smashing the
                       door.  Not significant enough to worry about; perhaps
                       the Key's magic is more powerful for monsters? */
                    here->doormask &= ~D_TRAPPED;
                    btrapped = FALSE;
                }
                if ((here->doormask & (D_LOCKED | D_CLOSED)) != 0
                    && SPWQ(ptr, SPW_AMORPHOUS, amorphous(ptr))) {
                    if (flags.verbose && canseemon(mtmp))
                        pline("%s %s under the door.", Monnam(mtmp),
                              (ptr == &mons[PM_FOG_CLOUD]
                               || ptr->mlet == S_LIGHT) ? "flows" : "oozes");
                } else if (here->doormask & D_LOCKED && can_unlock) {
                    if (btrapped) {
                        here->doormask = D_NODOOR;
                        newsym(mtmp->mx, mtmp->my);
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                        if (mb_trapped(mtmp))
                            return 2;
                    } else {
                        if (flags.verbose) {
                            if (observeit)
                                pline("%s unlocks and opens a door.",
                                      Monnam(mtmp));
                            else if (canseeit)
                                You_see("a door unlock and open.");
                            else if (!Deaf)
                                You_hear("a door unlock and open.");
                        }
                        here->doormask = D_ISOPEN;
                        /* newsym(mtmp->mx, mtmp->my); */
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                    }
                } else if (here->doormask == D_CLOSED && can_open) {
                    if (btrapped) {
                        here->doormask = D_NODOOR;
                        newsym(mtmp->mx, mtmp->my);
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                        if (mb_trapped(mtmp))
                            return 2;
                    } else {
                        if (flags.verbose) {
                            if (observeit)
                                pline("%s opens a door.", Monnam(mtmp));
                            else if (canseeit)
                                You_see("a door open.");
                            else if (!Deaf)
                                You_hear("a door open.");
                        }
                        here->doormask = D_ISOPEN;
                        /* newsym(mtmp->mx, mtmp->my); */  /* done below */
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                    }
                } else if (here->doormask & (D_LOCKED | D_CLOSED)) {
                    /* mfndpos guarantees this must be a doorbuster */
                    if (btrapped) {
                        here->doormask = D_NODOOR;
                        newsym(mtmp->mx, mtmp->my);
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                        if (mb_trapped(mtmp))
                            return 2;
                    } else {
                        if (flags.verbose) {
                            if (observeit)
                                pline("%s smashes down a door.",
                                      Monnam(mtmp));
                            else if (canseeit)
                                You_see("a door crash open.");
                            else if (!Deaf)
                                You_hear("a door crash open.");
                        }
                        if ((here->doormask & D_LOCKED) != 0 && !rn2(2))
                            here->doormask = D_NODOOR;
                        else
                            here->doormask = D_BROKEN;
                        /* newsym(mtmp->mx, mtmp->my); */  /* done below */
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                    }
                    /* if it's a shop door, schedule repair */
                    if (mt2_in_shop(mtmp->mx, mtmp->my)) /* v1.9: same predicate */
                        add_damage(mtmp->mx, mtmp->my, 0L);
                }
            } else if (TYP_AT(mtmp->mx, mtmp->my) == IRONBARS) {
                /* As of 3.6.2: was using may_dig() but it doesn't handle bars */
                if (!(NH_TILE(mtmp->mx, mtmp->my).wall_info & W_NONDIGGABLE)
                    && (dmgtype(ptr, AD_RUST) || dmgtype(ptr, AD_CORR))) {
                    if (canseemon(mtmp))
                        pline("%s eats through the iron bars.", Monnam(mtmp));
                    dissolve_bars(mtmp->mx, mtmp->my);
                    return 3;
                } else if (flags.verbose && canseemon(mtmp))
                    Norep("%s %s %s the iron bars.", Monnam(mtmp),
                          /* pluralization fakes verb conjugation */
                          makeplural(locomotion(ptr, "pass")),
                          SPWQ(ptr, SPW_PASSWALL, passes_walls(ptr)) ? "through" : "between");
            }


            /* can_tunnel and u.uswallow: excluded */
            nh_newsym_moved_far(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {
            /* recompute the likes tests, in case we polymorphed
             * or if the "likegold" case got taken above */
            if (setlikes) {
                int pctload = (curr_mon_load(mtmp) * 100) / max_mon_load(mtmp);

                /* look for gold or jewels nearby */
                likegold = (SPWQ(ptr, SPW_LIKEGOLD, likes_gold(ptr)) && pctload < 95);
                likegems = (SPWQ(ptr, SPW_LIKEGEMS, likes_gems(ptr)) && pctload < 85);
                uses_items =
                    (!SPWQ(ptr, SPW_MINDLESS, mindless(ptr)) && !SPWQ(ptr, SPW_ANIMAL, is_animal(ptr)) && pctload < 75);
                likeobjs = (SPWQ(ptr, SPW_LIKEOBJS, likes_objs(ptr)) && pctload < 75);
                likemagic = (SPWQ(ptr, SPW_LIKEMAGIC, likes_magic(ptr)) && pctload < 85);
                likerock = (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)) && pctload < 50 && !Sokoban);
                conceals = SPWQ(ptr, SPW_HIDESUNDER, hides_under(ptr));
            }

            /* Maybe a rock mole just ate some metal object */
            if (metallivorous(ptr)) {
                if (meatmetal(mtmp) == 2)
                    return 2; /* it died */
            }

            if (g_at(mtmp->mx, mtmp->my) && likegold)
                mpickgold(mtmp);

            /* Maybe a cube ate just about anything */
            if (ptr == &mons[PM_GELATINOUS_CUBE]) {
                if (meatobj(mtmp) == 2)
                    return 2; /* it died */
            }

            if (!mt2_in_shop(mtmp->mx, mtmp->my) || !rn2(25)) { /* v1.9: same predicate */
                boolean picked = FALSE;

                if (likeobjs)
                    picked |= mpickstuff(mtmp, practical);
                if (likemagic)
                    picked |= mpickstuff(mtmp, magical);
                if (likerock)
                    picked |= mpickstuff(mtmp, boulder_class);
                if (likegems)
                    picked |= mpickstuff(mtmp, gem_class);
                if (uses_items)
                    picked |= mpickstuff(mtmp, (char *) 0);
                if (picked)
                    mmoved = 3;
            }

            if (mtmp->minvis) {
                newsym(mtmp->mx, mtmp->my);
                if (mtmp->wormno)
                    see_wsegs(mtmp);
            }
        }
        if (SPWQ(ptr, SPW_HIDESUNDER, hides_under(ptr)) || ptr->mlet == S_EEL) {
            /* Always set--or reset--mundetected if it's already hidden
               (just in case the object it was hiding under went away);
               usually set mundetected unless monster can't move.  */
            if (mtmp->mundetected
                || (mtmp->mcanmove && !mtmp->msleeping && rn2(5)))
                (void) hideunder(mtmp);
            newsym(mtmp->mx, mtmp->my);
        }
        /* isshk: excluded */
    }
    return mmoved;
}

/* dochug() for an eligible monster: the pre-move chain is inert at this distance (PLAN.md KERNEL DECISIONS 2) */
static int
dochug_fast(mtmp)
register struct monst *mtmp;
{
    register struct permonst *mdat = mtmp->data;
    register int tmp = 0;
    int inrange = 0, nearby = 0, scared = 0;

    if (head_engr) /* wipe_engr_at() is a no-op without an engraving on the level */
        wipe_engr_at(mtmp->mx, mtmp->my, 1, FALSE);
    set_apparxy(mtmp); /* believed hero position (original function: exact for Invis/Displaced) */
    distfleeck(mtmp, &inrange, &nearby, &scared); /* not adjacent: nearby = scared = 0; inrange feeds the wield block */
    if (inrange)
        nh_mt2_hero_valid = 0; /* items, spells and attacks below may change hero properties */
    if (dist2(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy) <= 36) {
        if (find_defensive(mtmp)) {
            if (use_defensive(mtmp) != 0)
                return 1;
        } else if (find_misc(mtmp)) {
            if (use_misc(mtmp) != 0)
                return 1;
        }
    } else
        nh_muse_far_misc(); /* find_defensive() FALSE before any effect (dist2 > 25); find_misc() clears m.misc then FALSE (dist2 > 36) */

    /* If monster is nearby you, and has to wield a weapon, do so.   This
     * costs the monster a move, of course.
     */
    if ((!mtmp->mpeaceful || Conflict) && inrange
        && dist2(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy) <= 8
        && SPWQ(mdat, SPW_WEAPATTK, attacktype(mdat, AT_WEAP))) {
        struct obj *mw_tmp;

        /* The scared check is necessary.  Otherwise a monster that is
         * one square near the player but fleeing into a wall would keep
         * switching between pick-axe and weapon.  If monster is stuck
         * in a trap, prefer ranged weapon (wielding is done in thrwmu).
         * This may cost the monster an attack, but keeps the monster
         * from switching back and forth if carrying both.
         */
        mw_tmp = MON_WEP(mtmp);
        if (!(scared && mw_tmp && is_pick(mw_tmp))
            && mtmp->weapon_check == NEED_WEAPON
            && !(mtmp->mtrapped && !nearby && select_rwep(mtmp))) {
            mtmp->weapon_check = NEED_HTH_WEAPON;
            if (mon_wield_item(mtmp) != 0)
                return 0;
        }
    }


    /* Demonic Blackmail! */
    if (nearby && mdat->msound == MS_BRIBE && mtmp->mpeaceful && !mtmp->mtame
        && !u.uswallow) {
        if (mtmp->mux != u.ux || mtmp->muy != u.uy) {
            pline("%s whispers at thin air.",
                  cansee(mtmp->mux, mtmp->muy) ? Monnam(mtmp) : "It");

            if (is_demon(youmonst.data)) {
                /* "Good hunting, brother" */
                if (!tele_restrict(mtmp))
                    (void) rloc(mtmp, TRUE);
            } else {
                mtmp->minvis = mtmp->perminvis = 0;
                /* Why?  For the same reason in real demon talk */
                pline("%s gets angry!", Amonnam(mtmp));
                mtmp->mpeaceful = 0;
                set_malign(mtmp);
                /* since no way is an image going to pay it off */
            }
        } else if (demon_talk(mtmp))
            return 1; /* you paid it off */
    }

    /*  Now the actual movement phase
     */

    if (!nearby || mtmp->mflee || scared || mtmp->mconf || mtmp->mstun
        || (mtmp->minvis && !rn2(3))
        || (mdat->mlet == S_LEPRECHAUN && !findgold(invent)
            && (findgold(mtmp->minvent) || rn2(2)))
        || (SPWQ(mdat, SPW_WANDER, is_wanderer(mdat)) && !rn2(4)) || (Conflict && !mtmp->iswiz)
        || (!mtmp->mcansee && !rn2(4)) || mtmp->mpeaceful) {
        /* Possibly cast an undirected spell if not attacking you */
        /* note that most of the time castmu() will pick a directed
           spell and do nothing, so the monster moves normally */
        /* arbitrary distance restriction to keep monster far away
           from you from having cast dozens of sticks-to-snakes
           or similar spells by the time you reach it */
        if (dist2(mtmp->mx, mtmp->my, u.ux, u.uy) <= 49
            && !mtmp->mspec_used) {
            struct attack *a;

            for (a = &mdat->mattk[0]; a < &mdat->mattk[NATTK]; a++) {
                if (a->aatyp == AT_MAGC
                    && (a->adtyp == AD_SPEL || a->adtyp == AD_CLRC)) {
                    if (castmu(mtmp, a, FALSE, FALSE)) {
                        tmp = 3;
                        break;
                    }
                }
            }
        }

        tmp = m_move_fast(mtmp);
#ifdef NH_MT2_TRACE
        if (nh_mt2_trace_elig && nh_mt2_trace_fp && mt2_trace_on()) fprintf(nh_mt2_trace_fp, "E%d  after m_move id%u tmp%d rng%d\n", nh_ctx_serial, mtmp->m_id, tmp, nle_rng_state(0)->n);
#endif
        if (tmp != 2) {
            if (dist2(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy) > (BOLT_LIM * BOLT_LIM)) {
                (void) rn2(5); /* distfleeck() recalc out of range: its draw and its three results */
                inrange = nearby = scared = 0;
            } else {
                nh_mt2_hero_valid = 0; /* the near tail (attacks) may change hero properties */
                distfleeck(mtmp, &inrange, &nearby, &scared); /* recalc */
            }
        }

        switch (tmp) { /* for pets, cases 0 and 3 are equivalent */
        case 0: /* no movement, but it can still attack you */
        case 3: /* absolutely no movement */
            /* vault guard might have vanished */
            if (mtmp->isgd && (DEADMONSTER(mtmp) || mtmp->mx == 0))
                return 1; /* behave as if it died */
            /* During hallucination, monster appearance should
             * still change - even if it doesn't move.
             */
            if (Hallucination)
                newsym(mtmp->mx, mtmp->my);
            break;
        case 1: /* monster moved */
            /* Maybe it stepped on a trap and fell asleep... */
            if (mtmp->msleeping || !mtmp->mcanmove)
                return 0;
            /* Monsters can move and then shoot on same turn;
               our hero can't.  Is that fair? */
            if (!nearby && (SPWQ(mdat, SPW_RANGED, ranged_attk(mdat)) || find_offensive(mtmp)))
                break;
            /* engulfer/grabber checks */
            if (mtmp == u.ustuck) {
                /* a monster that's digesting you can move at the
                 * same time -dlc
                 */
                if (u.uswallow)
                    return mattacku(mtmp);
                /* if confused grabber has wandered off, let go */
                if (distu(mtmp->mx, mtmp->my) > 2)
                    unstuck(mtmp);
            }
            return 0;
        case 2: /* monster died */
            return 1;
        }
    }

    if (!mtmp->mpeaceful || (Conflict && !resist(mtmp, RING_CLASS, 0, 0))) {
        if (inrange && !SPWQ(mdat, SPW_NOATTACKS, noattacks(mdat))
            && (Upolyd ? u.mh : u.uhp) > 0 && !scared && tmp != 3)
            if (mattacku(mtmp))
                return 1;
        if (mtmp->wormno)
            wormhitu(mtmp);
    }
    if (!mtmp->msleeping && mtmp->mcanmove && nearby)
        quest_talk(mtmp);
    if (inrange && mtmp->data->msound == MS_CUSS && !mtmp->mpeaceful
        && couldsee(mtmp->mx, mtmp->my) && !mtmp->minvis && !rn2(5))
        cuss(mtmp);

    return (tmp == 2);
}

boolean
m_digweapon_check(mtmp, nix, niy)
struct monst *mtmp;
xchar nix,niy;
{
    boolean can_tunnel = 0;
    struct obj *mw_tmp = MON_WEP(mtmp);

    if (!Is_rogue_level(&u.uz))
        can_tunnel = tunnels(mtmp->data);

    if (can_tunnel && needspick(mtmp->data) && !mwelded(mw_tmp)
        && (may_dig(nix, niy) || closed_door(nix, niy))) {
        /* may_dig() is either IS_STWALL or IS_TREE */
        if (closed_door(nix, niy)) {
            if (!mw_tmp
                || !is_pick(mw_tmp)
                || !is_axe(mw_tmp))
                mtmp->weapon_check = NEED_PICK_OR_AXE;
        } else if (IS_TREE(TYP_AT(nix, niy))) {
            if (!(mw_tmp = MON_WEP(mtmp)) || !is_axe(mw_tmp))
                mtmp->weapon_check = NEED_AXE;
        } else if (IS_STWALL(TYP_AT(nix, niy))) {
            if (!(mw_tmp = MON_WEP(mtmp)) || !is_pick(mw_tmp))
                mtmp->weapon_check = NEED_PICK_AXE;
        }
        if (mtmp->weapon_check >= NEED_PICK_AXE && mon_wield_item(mtmp))
            return TRUE;
    }
    return FALSE;
}

/* Return values:
 * 0: did not move, but can still attack and do other stuff.
 * 1: moved, possibly can attack.
 * 2: monster died.
 * 3: did not move, and can't do anything else either.
 */

/* Preserve fobj order. A mutation during iteration switches that iterator to
 * the original linked-list walk from prev->nobj; never rebuild under a cursor. */
void
nh_fobj_invalidate(void)
{
    nh_fobj_valid = 0;
    nh_fobj_generation++;
}

/* The index lives in the window [nh_fobj_lo, nh_fobj_lo + nh_fobj_count) parked
 * at the top of the arrays, so place_object (a chain prepend) is one store and
 * remove_object shifts only the newer prefix. Other chain edits still invalidate. */
static void
nh_fobj_build(void)
{
    struct obj *o;
    int n = 0;
    for (o = fobj; o; o = o->nobj) {
        if (n == 2048) { nh_fobj_count = -1; nh_fobj_valid = 1; return; }
        nh_fobj_ptr[n] = o;
        nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
        n++;
    }
    if (n && n < 2048) {
        memmove(nh_fobj_ptr + 2048 - n, nh_fobj_ptr, n * sizeof nh_fobj_ptr[0]);
        memmove(nh_fobj_x + 2048 - n, nh_fobj_x, n * sizeof nh_fobj_x[0]);
        memmove(nh_fobj_y + 2048 - n, nh_fobj_y, n * sizeof nh_fobj_y[0]);
    }
    nh_fobj_lo = 2048 - n; nh_fobj_count = n; nh_fobj_valid = 1;
    for (n = nh_fobj_lo; n < 2048; n++) nh_fobj_ptr[n]->nh_fidx = n;
}

/* Floor objects inside the box, in fobj order (ascending index): the search loop can then run its original body over them.
   Returns -1 when the index is unavailable (too many objects) or the box holds more than MT2_MAXOBJ objects: use the cursor. */
static int
mt2_box_objects(int lx, int hx, int ly, int hy, struct obj **list)
{
    unsigned int rows = (2U << hy) - (1U << ly);
    int x, n = 0, i, j;
    struct obj *o, *t;
    if (!nh_fobj_valid) nh_fobj_build();
    if (nh_fobj_count < 0) return -1;
    for (x = lx; x <= hx; x++) {
        unsigned int bits = level.move_columns[x + 1].obj & rows;
        while (bits) {
            int y = __builtin_ctz(bits);
            bits &= bits - 1;
            for (o = level.objs[x][y]; o; o = o->nexthere) {
                if (n == MT2_MAXOBJ) return -1;
                list[n++] = o;
            }
        }
    }
    for (i = 1; i < n; i++) { /* insertion sort by fobj position */
        t = list[i];
        for (j = i; j > 0 && list[j - 1]->nh_fidx > t->nh_fidx; j--) list[j] = list[j - 1];
        list[j] = t;
    }
    return n;
}

void
nh_fobj_placed(struct obj *o)
{
    nh_fobj_generation++;
    if (!nh_fobj_valid || nh_fobj_count < 0) return;
    if (nh_fobj_lo == 0) { nh_fobj_valid = 0; return; }
    nh_fobj_lo--;
    nh_fobj_ptr[nh_fobj_lo] = o;
    o->nh_fidx = nh_fobj_lo;
    nh_fobj_x[nh_fobj_lo] = o->ox; nh_fobj_y[nh_fobj_lo] = o->oy;
    nh_fobj_count++;
}

void
nh_fobj_removed(struct obj *o)
{
    int i, lo = nh_fobj_lo, hi;
    nh_fobj_generation++;
    if (!nh_fobj_valid || nh_fobj_count < 0) return;
    hi = lo + nh_fobj_count;
    for (i = lo; i < hi; i++)
        if (nh_fobj_ptr[i] == o) break;
    if (i == hi) { nh_fobj_valid = 0; return; }
    memmove(nh_fobj_ptr + lo + 1, nh_fobj_ptr + lo, (i - lo) * sizeof nh_fobj_ptr[0]);
    memmove(nh_fobj_x + lo + 1, nh_fobj_x + lo, (i - lo) * sizeof nh_fobj_x[0]);
    memmove(nh_fobj_y + lo + 1, nh_fobj_y + lo, (i - lo) * sizeof nh_fobj_y[0]);
    for (hi = lo + 1; hi <= i; hi++) nh_fobj_ptr[hi]->nh_fidx = hi;
    nh_fobj_lo++; nh_fobj_count--;
}

struct obj *
nh_fobj_next(struct nh_fobj_cursor *cursor, struct obj *prev,
             int lx, int hx, int ly, int hy)
{
    struct obj *o;
    if (!prev) {
        if (!nh_fobj_valid) nh_fobj_build();
        cursor->generation = nh_fobj_generation;
        cursor->index = nh_fobj_lo;
        cursor->mask = 0;
        cursor->fallback = nh_fobj_count < 0;
    } else if (cursor->generation != nh_fobj_generation) {
        cursor->fallback = 1;
    }
    if (cursor->fallback) {
        for (o = prev ? prev->nobj : fobj; o; o = o->nobj)
            if (o->ox >= lx && o->ox <= hx && o->oy >= ly && o->oy <= hy)
                return o;
        return (struct obj *) 0;
    }
#ifdef NLE_FOBJ_VERIFY
    if (!prev && nh_fobj_count >= 0) {
        int n = 0, bad = 0;
        for (o = fobj; o; o = o->nobj, n++)
            if (n >= nh_fobj_count || nh_fobj_ptr[nh_fobj_lo + n] != o
                || nh_fobj_x[nh_fobj_lo + n] != o->ox || nh_fobj_y[nh_fobj_lo + n] != o->oy) { bad = 1; break; }
        if (bad || n != nh_fobj_count) {
            fprintf(stderr, "FOBJ_MISMATCH turn=%ld n=%d count=%d lo=%d\n", moves, n, nh_fobj_count, nh_fobj_lo);
            nh_fobj_build();
            cursor->generation = nh_fobj_generation;
            cursor->index = nh_fobj_lo;
            cursor->fallback = nh_fobj_count < 0;
        }
    }
#endif
#ifdef __SSE2__
    /* Reject sixteen byte coordinates at once; the first matching entry still wins. */
    if (lx >= -128 && hx <= 127 && ly >= -128 && hy <= 127
        && lx <= hx && ly <= hy) {
        if (cursor->mask && cursor->lx == lx && cursor->hx == hx
            && cursor->ly == ly && cursor->hy == hy) {
            int bit = __builtin_ctz(cursor->mask);
            int i = cursor->base + bit;
            cursor->mask &= ~(1U << bit);
            cursor->index = i + 1;
            return nh_fobj_ptr[i];
        }
        cursor->mask = 0;
        __m128i xl = _mm_set1_epi8((char) lx), xh = _mm_set1_epi8((char) hx);
        __m128i yl = _mm_set1_epi8((char) ly), yh = _mm_set1_epi8((char) hy);
        while (cursor->index + 16 <= nh_fobj_lo + nh_fobj_count) {
            int i = cursor->index;
            __m128i x = _mm_loadu_si128((const __m128i *) (nh_fobj_x + i));
            __m128i y = _mm_loadu_si128((const __m128i *) (nh_fobj_y + i));
            __m128i reject = _mm_or_si128(
                _mm_or_si128(_mm_cmpgt_epi8(xl, x), _mm_cmpgt_epi8(x, xh)),
                _mm_or_si128(_mm_cmpgt_epi8(yl, y), _mm_cmpgt_epi8(y, yh)));
            unsigned int mask = (~(unsigned int) _mm_movemask_epi8(reject)) & 65535U;
            if (mask) {
                int bit = __builtin_ctz(mask);
                cursor->base = i;
                cursor->mask = mask & ~(1U << bit);
                cursor->lx = lx; cursor->hx = hx;
                cursor->ly = ly; cursor->hy = hy;
                i += bit;
                cursor->index = i + 1;
                return nh_fobj_ptr[i];
            }
            cursor->index += 16;
        }
    }
#endif
    cursor->mask = 0;
    while (cursor->index < nh_fobj_lo + nh_fobj_count) {
        int i = cursor->index++;
        if (nh_fobj_x[i] >= lx && nh_fobj_x[i] <= hx
            && nh_fobj_y[i] >= ly && nh_fobj_y[i] <= hy)
            return nh_fobj_ptr[i];
    }
    return (struct obj *) 0;
}

int
m_move(mtmp, after)
register struct monst *mtmp;
register int after;
{
    register int appr;
    xchar gx, gy, nix, niy, chcnt;
    int chi; /* could be schar except for stupid Sun-2 compiler */
    boolean likegold = 0, likegems = 0, likeobjs = 0, likemagic = 0,
            conceals = 0;
    boolean likerock = 0, can_tunnel = 0;
    boolean can_open = 0, can_unlock = 0, doorbuster = 0;
    boolean uses_items = 0, setlikes = 0;
    boolean avoid = FALSE;
    boolean better_with_displacing = FALSE;
    boolean sawmon = is_vampshifter(mtmp) ? canspotmon(mtmp) : FALSE; /* before it moved; only the fog-cloud shift reads it */
    struct permonst *ptr;
    struct monst *mtoo;
    schar mmoved = 0; /* not strictly nec.: chi >= 0 will do */
    long info[9];
    long flag;
    int omx = mtmp->mx, omy = mtmp->my;

    if (mtmp->mtrapped) {
        int i = mintrap(mtmp);

        if (i >= 2) {
            newsym(mtmp->mx, mtmp->my);
            return 2;
        } /* it died */
        if (i == 1)
            return 0; /* still in trap, so didn't move */
    }
    ptr = mtmp->data; /* mintrap() can change mtmp->data -dlc */

    if (mtmp->meating) {
        mtmp->meating--;
        if (mtmp->meating <= 0)
            finish_meating(mtmp);
        return 3; /* still eating */
    }
    if (SPWQ(ptr, SPW_HIDESUNDER, hides_under(ptr)) && OBJ_AT(mtmp->mx, mtmp->my) && rn2(10))
        return 0; /* do not leave hiding place */

#ifdef NH_MT2_CG
    if (nh_mt2_cur_elig) mt2_window_stats(mtmp);
#endif
    set_apparxy(mtmp);
    /* where does mtmp think you are? */
    /* Not necessary if m_move called from this file, but necessary in
     * other calls of m_move (ex. leprechauns dodging)
     */
    if (!Is_rogue_level(&u.uz))
        can_tunnel = SPWQ(ptr, SPW_TUNNELS, tunnels(ptr));
    can_open = !(SPWQ(ptr, SPW_NOHANDS, nohands(ptr)) || SPWQ(ptr, SPW_VERYSMALL, verysmall(ptr)));
    can_unlock =
        ((can_open && monhaskey(mtmp, TRUE)) || mtmp->iswiz || SPWQ(ptr, SPW_RIDER, is_rider(ptr)));
    doorbuster = SPWQ(ptr, SPW_GIANT, is_giant(ptr));
    if (mtmp->wormno)
        goto not_special;
    /* my dog gets special treatment */
    if (mtmp->mtame) {
        mmoved = dog_move(mtmp, after);
        goto postmov;
    }

    /* likewise for shopkeeper */
    if (mtmp->isshk) {
        mmoved = shk_move(mtmp);
        if (mmoved == -2)
            return 2;
        if (mmoved >= 0)
            goto postmov;
        mmoved = 0; /* follow player outside shop */
    }

    /* and for the guard */
    if (mtmp->isgd) {
        mmoved = gd_move(mtmp);
        if (mmoved == -2)
            return 2;
        if (mmoved >= 0)
            goto postmov;
        mmoved = 0;
    }

    /* and the acquisitive monsters get special treatment */
    if (SPWQ(ptr, SPW_COVETOUS, is_covetous(ptr))) {
        xchar tx = STRAT_GOALX(mtmp->mstrategy),
              ty = STRAT_GOALY(mtmp->mstrategy);
        struct monst *intruder = m_at(tx, ty);
        /*
         * if there's a monster on the object or in possession of it,
         * attack it.
         */
        if ((dist2(mtmp->mx, mtmp->my, tx, ty) < 2) && intruder
            && (intruder != mtmp)) {
            notonhead = (intruder->mx != tx || intruder->my != ty);
            if (mattackm(mtmp, intruder) == 2)
                return 2;
            mmoved = 1;
        } else
            mmoved = 0;
        goto postmov;
    }

    /* and for the priest */
    if (mtmp->ispriest) {
        mmoved = pri_move(mtmp);
        if (mmoved == -2)
            return 2;
        if (mmoved >= 0)
            goto postmov;
        mmoved = 0;
    }

#ifdef MAIL
    if (ptr == &mons[PM_MAIL_DAEMON]) {
        if (!Deaf && canseemon(mtmp))
            verbalize("I'm late!");
        mongone(mtmp);
        return 2;
    }
#endif

    /* teleport if that lies in our nature */
    if (ptr == &mons[PM_TENGU] && !rn2(5) && !mtmp->mcan
        && !tele_restrict(mtmp)) {
        if (mtmp->mhp < 7 || mtmp->mpeaceful || rn2(2))
            (void) rloc(mtmp, TRUE);
        else
            mnexto(mtmp);
        mmoved = 1;
        goto postmov;
    }
 not_special:
    if (u.uswallow && !mtmp->mflee && u.ustuck != mtmp)
        return 1;
    omx = mtmp->mx;
    omy = mtmp->my;
    gx = mtmp->mux;
    gy = mtmp->muy;
    appr = mtmp->mflee ? -1 : 1;
    if (mtmp->mconf || (u.uswallow && mtmp == u.ustuck)) {
        appr = 0;
    } else {
        struct obj *lepgold, *ygold;
        boolean should_see = (couldsee(omx, omy)
                              && (NH_TILE(gx, gy).lit || !NH_TILE(omx, omy).lit)
                              && (dist2(omx, omy, gx, gy) <= 36));

        if (!mtmp->mcansee
            || (should_see && Invis && !SPWQ(ptr, SPW_PERCEIVES, perceives(ptr)) && rn2(11))
            || is_obj_mappear(&youmonst,STRANGE_OBJECT) || u.uundetected
            || (is_obj_mappear(&youmonst,GOLD_PIECE) && !SPWQ(ptr, SPW_LIKEGOLD, likes_gold(ptr)))
            || (mtmp->mpeaceful && !mtmp->isshk) /* allow shks to follow */
            || ((monsndx(ptr) == PM_STALKER || ptr->mlet == S_BAT
                 || ptr->mlet == S_LIGHT) && !rn2(3)))
            appr = 0;

        if (monsndx(ptr) == PM_LEPRECHAUN && (appr == 1)
            && ((lepgold = findgold(mtmp->minvent))
                && (lepgold->quan
                    > ((ygold = findgold(invent)) ? ygold->quan : 0L))))
            appr = -1;

        if (!should_see && can_track(ptr)) {
            register coord *cp;

            cp = gettrack(omx, omy);
            if (cp) {
                gx = cp->x;
                gy = cp->y;
            }
        }
    }

    if ((!mtmp->mpeaceful || !rn2(10)) && (!Is_rogue_level(&u.uz))) {
        boolean in_line = (lined_up(mtmp)
               && (distmin(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy)
                   <= (throws_rocks(youmonst.data) ? 20 : ACURRSTR / 2 + 1)));

        if (appr != 1 || !in_line) {
            /* Monsters in combat won't pick stuff up, avoiding the
             * situation where you toss arrows at it and it has nothing
             * better to do than pick the arrows up.
             */
            register int pctload =
                (curr_mon_load(mtmp) * 100) / max_mon_load(mtmp);

            /* look for gold or jewels nearby */
            likegold = (SPWQ(ptr, SPW_LIKEGOLD, likes_gold(ptr)) && pctload < 95);
            likegems = (SPWQ(ptr, SPW_LIKEGEMS, likes_gems(ptr)) && pctload < 85);
            uses_items = (!SPWQ(ptr, SPW_MINDLESS, mindless(ptr)) && !SPWQ(ptr, SPW_ANIMAL, is_animal(ptr)) && pctload < 75);
            likeobjs = (SPWQ(ptr, SPW_LIKEOBJS, likes_objs(ptr)) && pctload < 75);
            likemagic = (SPWQ(ptr, SPW_LIKEMAGIC, likes_magic(ptr)) && pctload < 85);
            likerock = (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)) && pctload < 50 && !Sokoban);
            conceals = SPWQ(ptr, SPW_HIDESUNDER, hides_under(ptr));
            setlikes = TRUE;
        }
    }
    if (appr == 0) MT2C(C_APPR0);
    if (likegold || likegems || likeobjs || likemagic || likerock || conceals) MT2C(C_INTEREST);
    if (uses_items) MT2C(C_USESITEMS);

#define SQSRCHRADIUS 5

    {
        register int minr = SQSRCHRADIUS; /* not too far away */
        register struct obj *otmp;
        register int xx, yy;
        int oomx, oomy, lmx, lmy;
        struct nh_fobj_cursor cursor;

        /* cut down the search radius if it thinks character is closer. */
        if (distmin(mtmp->mux, mtmp->muy, omx, omy) < SQSRCHRADIUS
            && !mtmp->mpeaceful)
            minr--;
        /* guards shouldn't get too distracted */
        if (!mtmp->mpeaceful && SPWQ(ptr, SPW_MERC, is_mercenary(ptr)))
            minr = 1;

        if ((likegold || likegems || likeobjs || likemagic || likerock
             || conceals) && (!*in_rooms(omx, omy, SHOPBASE)
                              || (!rn2(25) && !mtmp->isshk))) {
 look_for_obj:
            MT2C(C_SEARCH);
            oomx = min(COLNO - 1, omx + minr);
            oomy = min(ROWNO - 1, omy + minr);
            lmx = max(1, omx - minr);
            lmy = max(0, omy - minr);
            for (otmp = nh_fobj_next(&cursor, (struct obj *) 0, lmx, oomx, lmy, oomy);
                 otmp;
                 otmp = nh_fobj_next(&cursor, otmp, lmx, oomx, lmy, oomy)) {
                /* monsters may pick rocks up, but won't go out of their way
                   to grab them; this might hamper sling wielders, but it cuts
                   down on move overhead by filtering out most common item */
                MT2C(C_SEARCHOBJ);
                if (otmp->otyp == ROCK)
                    continue;
                xx = otmp->ox;
                yy = otmp->oy;
                /* Nymphs take everything.  Most other creatures should not
                 * pick up corpses except as a special case like in
                 * searches_for_item().  We need to do this check in
                 * mpickstuff() as well.
                 */
                if (xx >= lmx && xx <= oomx && yy >= lmy && yy <= oomy) {
                    /* don't get stuck circling around object that's
                       underneath an immobile or hidden monster;
                       paralysis victims excluded */
                    if ((mtoo = m_at(xx, yy)) != 0
                        && (mtoo->msleeping || mtoo->mundetected
                            || (mtoo->mappearance && !mtoo->iswiz)
                            || !mtoo->data->mmove))
                        continue;
                    /* the mfndpos() test for whether to allow a move to a
                       water location accepts flyers, but they can't reach
                       underwater objects, so being able to move to a spot
                       is insufficient for deciding whether to do so */
                    if ((is_pool(xx, yy) && !SPWQ(ptr, SPW_SWIMMER, is_swimmer(ptr)))
                        || (is_lava(xx, yy) && !SPWQ(ptr, SPW_LIKELAVA, likes_lava(ptr))))
                        continue;

                    if (((likegold && otmp->oclass == COIN_CLASS)
                         || (likeobjs && index(practical, otmp->oclass)
                             && (otmp->otyp != CORPSE
                                 || (ptr->mlet == S_NYMPH
                                     && !is_rider(&mons[otmp->corpsenm]))))
                         || (likemagic && index(magical, otmp->oclass))
                         || (uses_items && searches_for_item(mtmp, otmp))
                         || (likerock && otmp->otyp == BOULDER)
                         || (likegems && otmp->oclass == GEM_CLASS
                             && objects[otmp->otyp].oc_material != MINERAL)
                         || (conceals && !cansee(otmp->ox, otmp->oy))
                         || (ptr == &mons[PM_GELATINOUS_CUBE]
                             && !index(indigestion, otmp->oclass)
                             && !(otmp->otyp == CORPSE
                                  && touch_petrifies(&mons[otmp->corpsenm]))))
                        && touch_artifact(otmp, mtmp)) {
                        if (can_carry(mtmp, otmp) > 0
                            && (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)) || !sobj_at(BOULDER, xx, yy))
                            && (!SPWQ(ptr, SPW_UNICORN, is_unicorn(ptr))
                                || objects[otmp->otyp].oc_material == GEMSTONE)
                            /* Don't get stuck circling an Elbereth */
                            && !onscary(xx, yy, mtmp)) {
                            minr = distmin(omx, omy, xx, yy);
                            oomx = min(COLNO - 1, omx + minr);
                            oomy = min(ROWNO - 1, omy + minr);
                            lmx = max(1, omx - minr);
                            lmy = max(0, omy - minr);
                            gx = otmp->ox;
                            gy = otmp->oy;
                            MT2C(C_TARGET);
                            if (gx == omx && gy == omy) {
                                mmoved = 3; /* actually unnecessary */
                                goto postmov;
                            }
                        }
                    }
                }
            }
        } else if (likegold) {
            /* don't try to pick up anything else, but use the same loop */
            uses_items = 0;
            likegems = likeobjs = likemagic = likerock = conceals = 0;
            goto look_for_obj;
        }

        if (minr < SQSRCHRADIUS && appr == -1) {
            if (distmin(omx, omy, mtmp->mux, mtmp->muy) <= 3) {
                gx = mtmp->mux;
                gy = mtmp->muy;
            } else
                appr = 1;
        }
    }

    /* don't tunnel if hostile and close enough to prefer a weapon */
    if (can_tunnel && SPWQ(ptr, SPW_NEEDSPICK, needspick(ptr))
        && ((!mtmp->mpeaceful || Conflict)
            && dist2(mtmp->mx, mtmp->my, mtmp->mux, mtmp->muy) <= 8))
        can_tunnel = FALSE;

    nix = omx;
    niy = omy;
    flag = 0L;
    if (mtmp->mpeaceful && (!Conflict || resist(mtmp, RING_CLASS, 0, 0)))
        flag |= (ALLOW_SANCT | ALLOW_SSM);
    else
        flag |= ALLOW_U;
    if (SPWQ(ptr, SPW_MINION, is_minion(ptr)) || SPWQ(ptr, SPW_RIDER, is_rider(ptr)))
        flag |= ALLOW_SANCT;
    /* unicorn may not be able to avoid hero on a noteleport level */
    if (SPWQ(ptr, SPW_UNICORN, is_unicorn(ptr)) && !level.lflags.noteleport)
        flag |= NOTONL;
    if (SPWQ(ptr, SPW_PASSWALL, passes_walls(ptr)))
        flag |= (ALLOW_WALL | ALLOW_ROCK);
    if (SPWQ(ptr, SPW_PASSBARS, passes_bars(ptr)))
        flag |= ALLOW_BARS;
    if (can_tunnel)
        flag |= ALLOW_DIG;
    if (SPWQ(ptr, SPW_HUMAN, is_human(ptr)) || ptr == &mons[PM_MINOTAUR])
        flag |= ALLOW_SSM;
    if ((SPWQ(ptr, SPW_UNDEAD, is_undead(ptr)) && ptr->mlet != S_GHOST) || is_vampshifter(mtmp))
        flag |= NOGARLIC;
    if (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)))
        flag |= ALLOW_ROCK;
    if (can_open)
        flag |= OPENDOOR;
    if (can_unlock)
        flag |= UNLOCKDOOR;
    if (doorbuster)
        flag |= BUSTDOOR;
    {
        register int i, j, nx, ny, nearer;
        unsigned int trackmask;
        int jcnt, cnt;
        int ndist, nidist;
        register coord *mtrk;
        coord poss[9];

        cnt = mfndpos(mtmp, poss, info, flag);
        MT2C(C_CNT0 + (cnt > 8 ? 8 : cnt));
        chcnt = 0;
        jcnt = min(MTSZ, cnt - 1);
        trackmask = 0; /* neighbourhood bits of the recent track: the avoidance loop (and its RNG draw) only runs on a hit */
        for (j = 0; j < jcnt; j++)
            trackmask |= nh_move_position_bit(omx, omy, mtmp->mtrack[j].x, mtmp->mtrack[j].y);
        chi = -1;
        nidist = dist2(nix, niy, gx, gy);
        /* allow monsters be shortsighted on some levels for balance */
        if (!mtmp->mpeaceful && level.lflags.shortsighted
            && nidist > (couldsee(nix, niy) ? 144 : 36) && appr == 1)
            appr = 0;
        if (SPWQ(ptr, SPW_UNICORN, is_unicorn(ptr)) && level.lflags.noteleport) {
            /* on noteleport levels, perhaps we cannot avoid hero */
            for (i = 0; i < cnt; i++)
                if (!(info[i] & NOTONL))
                    avoid = TRUE;
        }
        better_with_displacing =
            should_displace(mtmp, poss, info, cnt, gx, gy);
        for (i = 0; i < cnt; i++) {
            if (avoid && (info[i] & NOTONL))
                continue;
            nx = poss[i].x;
            ny = poss[i].y;

            if ((info[i] & ALLOW_MDISP)
                && !(info[i] & ALLOW_M) && !better_with_displacing)
                continue;
            if (appr != 0 && (trackmask & nh_move_position_bit(omx, omy, nx, ny))) {
                MT2C(C_TRACKHIT);
                /* same draws in the same order: one rn2 per matching track entry, ascending, until the first nonzero */
                unsigned int hits = 0;
                mtrk = &mtmp->mtrack[0];
                for (j = 0; j < MTSZ; j++)
                    hits |= (unsigned int) ((j < jcnt) & (nx == mtrk[j].x) & (ny == mtrk[j].y)) << j;
                while (hits) {
                    j = __builtin_ctz(hits);
                    hits &= hits - 1;
                    if (rn2(4 * (cnt - j)))
                        goto nxti;
                }
            }

            ndist = dist2(nx, ny, gx, gy);
            nearer = (ndist < nidist);
            {
                /* The original predicate without its data-dependent branch: appr 1 takes a nearer cell, -1 a farther one,
                   0 draws rn2(++chcnt) for every candidate exactly as before, and the first candidate is always taken. */
                int take = appr ? ((nearer != (appr < 0)) | !mmoved) : (!rn2(++chcnt) | !mmoved);
                int m = -take;
                nix = (xchar) ((nx & m) | (nix & ~m));
                niy = (xchar) ((ny & m) | (niy & ~m));
                nidist = (ndist & m) | (nidist & ~m);
                chi = (i & m) | (chi & ~m);
                mmoved |= (schar) take;
            }
 nxti:
            ;
        }
        MT2_TRACE(mtmp, omx, omy, gx, gy, appr, cnt, poss, info, chi, nix, niy, mmoved);
    }

    if (mmoved) MT2C(C_MOVED); else MT2C(C_NOMOVE);
    if (mmoved) {
        register int j;

        if (mmoved == 1 && (u.ux != nix || u.uy != niy) && itsstuck(mtmp))
            return 3;

        if (mmoved == 1 && m_digweapon_check(mtmp, nix,niy))
            return 3;

        /* If ALLOW_U is set, either it's trying to attack you, or it
         * thinks it is.  In either case, attack this spot in preference to
         * all others.
         */
        /* Actually, this whole section of code doesn't work as you'd expect.
         * Most attacks are handled in dochug().  It calls distfleeck(), which
         * among other things sets nearby if the monster is near you--and if
         * nearby is set, we never call m_move unless it is a special case
         * (confused, stun, etc.)  The effect is that this ALLOW_U (and
         * mfndpos) has no effect for normal attacks, though it lets a
         * confused monster attack you by accident.
         */
        if (info[chi] & ALLOW_U) {
            nix = mtmp->mux;
            niy = mtmp->muy;
        }
        if (nix == u.ux && niy == u.uy) {
            mtmp->mux = u.ux;
            mtmp->muy = u.uy;
            return 0;
        }
        /* The monster may attack another based on 1 of 2 conditions:
         * 1 - It may be confused.
         * 2 - It may mistake the monster for your (displaced) image.
         * Pets get taken care of above and shouldn't reach this code.
         * Conflict gets handled even farther away (movemon()).
         */
        if ((info[chi] & ALLOW_M) || (nix == mtmp->mux && niy == mtmp->muy)) {
            struct monst *mtmp2;
            int mstatus;

            mtmp2 = m_at(nix, niy);

            notonhead = mtmp2 && (nix != mtmp2->mx || niy != mtmp2->my);
            /* note: mstatus returns 0 if mtmp2 is nonexistent */
            mstatus = mattackm(mtmp, mtmp2);

            if (mstatus & MM_AGR_DIED) /* aggressor died */
                return 2;

            if ((mstatus & MM_HIT) && !(mstatus & MM_DEF_DIED) && rn2(4)
                && mtmp2->movement >= NORMAL_SPEED) {
                mtmp2->movement -= NORMAL_SPEED;
                notonhead = 0;
                mstatus = mattackm(mtmp2, mtmp); /* return attack */
                if (mstatus & MM_DEF_DIED)
                    return 2;
            }
            return 3;
        }

        if ((info[chi] & ALLOW_MDISP)) {
            struct monst *mtmp2;
            int mstatus;

            mtmp2 = m_at(nix, niy);
            mstatus = mdisplacem(mtmp, mtmp2, FALSE);
            if ((mstatus & MM_AGR_DIED) || (mstatus & MM_DEF_DIED))
                return 2;
            if (mstatus & MM_HIT)
                return 1;
            return 3;
        }

        if (!m_in_out_region(mtmp, nix, niy))
            return 3;

        remove_monster(omx, omy);
        place_monster(mtmp, nix, niy);
        for (j = MTSZ - 1; j > 0; j--)
            mtmp->mtrack[j] = mtmp->mtrack[j - 1];
        mtmp->mtrack[0].x = omx;
        mtmp->mtrack[0].y = omy;
        /* Place a segment at the old position. */
        if (mtmp->wormno)
            worm_move(mtmp);
    } else {
        if (SPWQ(ptr, SPW_UNICORN, is_unicorn(ptr)) && rn2(2) && !tele_restrict(mtmp)) {
            (void) rloc(mtmp, TRUE);
            return 1;
        }
        if (mtmp->wormno)
            worm_nomove(mtmp);
    }
 postmov:
    if (mmoved == 3) MT2C(C_MMOVED3);
    if (mmoved == 1 || mmoved == 3) {
        boolean canseeit = cansee(mtmp->mx, mtmp->my);

        if (mmoved == 1) {
            /* normal monster move will already have <nix,niy>,
               but pet dog_move() with 'goto postmov' won't */
            nix = mtmp->mx, niy = mtmp->my;
            /* sequencing issue:  when monster movement decides that a
               monster can move to a door location, it moves the monster
               there before dealing with the door rather than after;
               so a vampire/bat that is going to shift to fog cloud and
               pass under the door is already there but transformation
               into fog form--and its message, when in sight--has not
               happened yet; we have to move monster back to previous
               location before performing the vamp_shift() to make the
               message happen at right time, then back to the door again
               [if we did the shift above, before moving the monster,
               we would need to duplicate it in dog_move()...] */
            if (is_vampshifter(mtmp) && !SPWQ(mtmp->data, SPW_AMORPHOUS, amorphous(mtmp->data))
                && IS_DOOR(TYP_AT(nix, niy))
                && ((NH_TILE(nix, niy).doormask & (D_LOCKED | D_CLOSED)) != 0)
                && can_fog(mtmp)) {
                if (sawmon) {
                    remove_monster(nix, niy);
                    place_monster(mtmp, omx, omy);
                    newsym(nix, niy), newsym(omx, omy);
                }
                if (vamp_shift(mtmp, &mons[PM_FOG_CLOUD], sawmon)) {
                    ptr = mtmp->data; /* update cached value */
                }
                if (sawmon) {
                    remove_monster(omx, omy);
                    place_monster(mtmp, nix, niy);
                    newsym(omx, omy), newsym(nix, niy);
                }
            }

            if (NH_SUMMARY(mtmp->mx, mtmp->my).move_trap_present) MT2C(C_DESTTRAP);
            if (IS_DOOR(TYP_AT(mtmp->mx, mtmp->my))) MT2C(C_DESTDOOR);
            if (nh_move_obj_at(mtmp->mx, mtmp->my)) MT2C(C_DESTOBJ);
            nh_newsym_moved(omx, omy); /* update the old position */
            if (mintrap(mtmp) >= 2) {
                if (mtmp->mx)
                    newsym(mtmp->mx, mtmp->my);
                return 2; /* it died */
            }
            ptr = mtmp->data; /* in case mintrap() caused polymorph */

            /* open a door, or crash through it, if 'mtmp' can */
            if (IS_DOOR(TYP_AT(mtmp->mx, mtmp->my))
                && !SPWQ(ptr, SPW_PASSWALL, passes_walls(ptr)) /* doesn't need to open doors */
                && !can_tunnel) {     /* taken care of below */
                struct rm *here = &NH_TILE(mtmp->mx, mtmp->my);
                boolean btrapped = (here->doormask & D_TRAPPED) != 0,
                        observeit = canseeit && canspotmon(mtmp);

                /* if mon has MKoT, disarm door trap; no message given */
                if (btrapped && has_magic_key(mtmp)) {
                    /* BUG: this lets a vampire or blob or a doorbuster
                       holding the Key disarm the trap even though it isn't
                       using that Key when squeezing under or smashing the
                       door.  Not significant enough to worry about; perhaps
                       the Key's magic is more powerful for monsters? */
                    here->doormask &= ~D_TRAPPED;
                    btrapped = FALSE;
                }
                if ((here->doormask & (D_LOCKED | D_CLOSED)) != 0
                    && SPWQ(ptr, SPW_AMORPHOUS, amorphous(ptr))) {
                    if (flags.verbose && canseemon(mtmp))
                        pline("%s %s under the door.", Monnam(mtmp),
                              (ptr == &mons[PM_FOG_CLOUD]
                               || ptr->mlet == S_LIGHT) ? "flows" : "oozes");
                } else if (here->doormask & D_LOCKED && can_unlock) {
                    if (btrapped) {
                        here->doormask = D_NODOOR;
                        newsym(mtmp->mx, mtmp->my);
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                        if (mb_trapped(mtmp))
                            return 2;
                    } else {
                        if (flags.verbose) {
                            if (observeit)
                                pline("%s unlocks and opens a door.",
                                      Monnam(mtmp));
                            else if (canseeit)
                                You_see("a door unlock and open.");
                            else if (!Deaf)
                                You_hear("a door unlock and open.");
                        }
                        here->doormask = D_ISOPEN;
                        /* newsym(mtmp->mx, mtmp->my); */
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                    }
                } else if (here->doormask == D_CLOSED && can_open) {
                    if (btrapped) {
                        here->doormask = D_NODOOR;
                        newsym(mtmp->mx, mtmp->my);
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                        if (mb_trapped(mtmp))
                            return 2;
                    } else {
                        if (flags.verbose) {
                            if (observeit)
                                pline("%s opens a door.", Monnam(mtmp));
                            else if (canseeit)
                                You_see("a door open.");
                            else if (!Deaf)
                                You_hear("a door open.");
                        }
                        here->doormask = D_ISOPEN;
                        /* newsym(mtmp->mx, mtmp->my); */  /* done below */
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                    }
                } else if (here->doormask & (D_LOCKED | D_CLOSED)) {
                    /* mfndpos guarantees this must be a doorbuster */
                    if (btrapped) {
                        here->doormask = D_NODOOR;
                        newsym(mtmp->mx, mtmp->my);
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                        if (mb_trapped(mtmp))
                            return 2;
                    } else {
                        if (flags.verbose) {
                            if (observeit)
                                pline("%s smashes down a door.",
                                      Monnam(mtmp));
                            else if (canseeit)
                                You_see("a door crash open.");
                            else if (!Deaf)
                                You_hear("a door crash open.");
                        }
                        if ((here->doormask & D_LOCKED) != 0 && !rn2(2))
                            here->doormask = D_NODOOR;
                        else
                            here->doormask = D_BROKEN;
                        /* newsym(mtmp->mx, mtmp->my); */  /* done below */
                        unblock_point(mtmp->mx, mtmp->my); /* vision */
                    }
                    /* if it's a shop door, schedule repair */
                    if (*in_rooms(mtmp->mx, mtmp->my, SHOPBASE))
                        add_damage(mtmp->mx, mtmp->my, 0L);
                }
            } else if (TYP_AT(mtmp->mx, mtmp->my) == IRONBARS) {
                /* As of 3.6.2: was using may_dig() but it doesn't handle bars */
                if (!(NH_TILE(mtmp->mx, mtmp->my).wall_info & W_NONDIGGABLE)
                    && (dmgtype(ptr, AD_RUST) || dmgtype(ptr, AD_CORR))) {
                    if (canseemon(mtmp))
                        pline("%s eats through the iron bars.", Monnam(mtmp));
                    dissolve_bars(mtmp->mx, mtmp->my);
                    return 3;
                } else if (flags.verbose && canseemon(mtmp))
                    Norep("%s %s %s the iron bars.", Monnam(mtmp),
                          /* pluralization fakes verb conjugation */
                          makeplural(locomotion(ptr, "pass")),
                          SPWQ(ptr, SPW_PASSWALL, passes_walls(ptr)) ? "through" : "between");
            }

            /* possibly dig */
            if (can_tunnel && mdig_tunnel(mtmp))
                return 2; /* mon died (position already updated) */

            /* set also in domove(), hack.c */
            if (u.uswallow && mtmp == u.ustuck
                && (mtmp->mx != omx || mtmp->my != omy)) {
                /* If the monster moved, then update */
                u.ux0 = u.ux;
                u.uy0 = u.uy;
                u.ux = mtmp->mx;
                u.uy = mtmp->my;
                swallowed(0);
            } else
                nh_newsym_moved(mtmp->mx, mtmp->my);
        }
        if (nh_move_obj_at(mtmp->mx, mtmp->my) && mtmp->mcanmove) {
            /* recompute the likes tests, in case we polymorphed
             * or if the "likegold" case got taken above */
            if (setlikes) {
                int pctload = (curr_mon_load(mtmp) * 100) / max_mon_load(mtmp);

                /* look for gold or jewels nearby */
                likegold = (SPWQ(ptr, SPW_LIKEGOLD, likes_gold(ptr)) && pctload < 95);
                likegems = (SPWQ(ptr, SPW_LIKEGEMS, likes_gems(ptr)) && pctload < 85);
                uses_items =
                    (!SPWQ(ptr, SPW_MINDLESS, mindless(ptr)) && !SPWQ(ptr, SPW_ANIMAL, is_animal(ptr)) && pctload < 75);
                likeobjs = (SPWQ(ptr, SPW_LIKEOBJS, likes_objs(ptr)) && pctload < 75);
                likemagic = (SPWQ(ptr, SPW_LIKEMAGIC, likes_magic(ptr)) && pctload < 85);
                likerock = (SPWQ(ptr, SPW_THROWSROCKS, throws_rocks(ptr)) && pctload < 50 && !Sokoban);
                conceals = SPWQ(ptr, SPW_HIDESUNDER, hides_under(ptr));
            }

            /* Maybe a rock mole just ate some metal object */
            if (metallivorous(ptr)) {
                if (meatmetal(mtmp) == 2)
                    return 2; /* it died */
            }

            if (g_at(mtmp->mx, mtmp->my) && likegold)
                mpickgold(mtmp);

            /* Maybe a cube ate just about anything */
            if (ptr == &mons[PM_GELATINOUS_CUBE]) {
                if (meatobj(mtmp) == 2)
                    return 2; /* it died */
            }

            if (!*in_rooms(mtmp->mx, mtmp->my, SHOPBASE) || !rn2(25)) {
                boolean picked = FALSE;

                if (likeobjs)
                    picked |= mpickstuff(mtmp, practical);
                if (likemagic)
                    picked |= mpickstuff(mtmp, magical);
                if (likerock)
                    picked |= mpickstuff(mtmp, boulder_class);
                if (likegems)
                    picked |= mpickstuff(mtmp, gem_class);
                if (uses_items)
                    picked |= mpickstuff(mtmp, (char *) 0);
                if (picked)
                    mmoved = 3;
            }

            if (mtmp->minvis) {
                newsym(mtmp->mx, mtmp->my);
                if (mtmp->wormno)
                    see_wsegs(mtmp);
            }
        }

        if (SPWQ(ptr, SPW_HIDESUNDER, hides_under(ptr)) || ptr->mlet == S_EEL) {
            /* Always set--or reset--mundetected if it's already hidden
               (just in case the object it was hiding under went away);
               usually set mundetected unless monster can't move.  */
            if (mtmp->mundetected
                || (mtmp->mcanmove && !mtmp->msleeping && rn2(5)))
                (void) hideunder(mtmp);
            newsym(mtmp->mx, mtmp->my);
        }
        if (mtmp->isshk) {
            after_shk_move(mtmp);
        }
    }
    return mmoved;
}

void
dissolve_bars(x, y)
register int x, y;
{
    SET_TYP_XY(x, y, (Is_special(&u.uz) || *in_rooms(x, y, 0)) ? ROOM : CORR);
    NH_TILE(x, y).rmflags = 0;
    newsym(x, y);
}

boolean
closed_door(x, y)
register int x, y;
{
    return (boolean) (IS_DOOR(TYP_AT(x, y))
                      && (NH_TILE(x, y).doormask & (D_LOCKED | D_CLOSED)));
}

boolean
accessible(x, y)
register int x, y;
{
    int levtyp = TYP_AT(x, y);

    /* use underlying terrain in front of closed drawbridge */
    if (levtyp == DRAWBRIDGE_UP)
        levtyp = db_under_typ(NH_TILE(x, y).drawbridgemask);

    return (boolean) (ACCESSIBLE(levtyp) && !closed_door(x, y));
}

/* decide where the monster thinks you are standing */
void
set_apparxy(mtmp)
register struct monst *mtmp;
{
    boolean notseen, gotu;
    register int disp, mx = mtmp->mux, my = mtmp->muy;

    /*
     * do cheapest and/or most likely tests first
     */

    /* pet knows your smell; grabber still has hold of you */
    if (mtmp->mtame || mtmp == u.ustuck)
        goto found_you;

    /* monsters which know where you are don't suddenly forget,
       if you haven't moved away */
    if (mx == u.ux && my == u.uy)
        goto found_you;

    notseen = (!mtmp->mcansee || (Invis && !SPWQ(mtmp->data, SPW_PERCEIVES, perceives(mtmp->data))));
    /* add cases as required.  eg. Displacement ... */
    if (notseen || Underwater) {
        /* Xorns can smell quantities of valuable metal
            like that in solid gold coins, treat as seen */
        if ((mtmp->data == &mons[PM_XORN]) && money_cnt(invent) && !Underwater)
            disp = 0;
        else
            disp = 1;
    } else if (Displaced) {
        disp = couldsee(mx, my) ? 2 : 1;
    } else
        disp = 0;
    if (!disp)
        goto found_you;

    /* without something like the following, invisibility and displacement
       are too powerful */
    gotu = notseen ? !rn2(3) : Displaced ? !rn2(4) : FALSE;

    if (!gotu) {
        register int try_cnt = 0;

        do {
            if (++try_cnt > 200)
                goto found_you; /* punt */
            mx = u.ux - disp + rn2(2 * disp + 1);
            my = u.uy - disp + rn2(2 * disp + 1);
        } while (!isok(mx, my)
                 || (disp != 2 && mx == mtmp->mx && my == mtmp->my)
                 || ((mx != u.ux || my != u.uy) && !SPWQ(mtmp->data, SPW_PASSWALL, passes_walls(mtmp->data))
                     && !(accessible(mx, my)
                          || (closed_door(mx, my)
                              && (can_ooze(mtmp) || can_fog(mtmp)))))
                 || !couldsee(mx, my));
    } else {
 found_you:
        mx = u.ux;
        my = u.uy;
    }

    mtmp->mux = mx;
    mtmp->muy = my;
}

/*
 * mon-to-mon displacement is a deliberate "get out of my way" act,
 * not an accidental bump, so we don't consider mstun or mconf in
 * undesired_disp().
 *
 * We do consider many other things about the target and its
 * location however.
 */
boolean
undesirable_disp(mtmp, x, y)
struct monst *mtmp; /* barging creature */
xchar x, y; /* spot 'mtmp' is considering moving to */
{
    boolean is_pet = (mtmp && mtmp->mtame && !mtmp->isminion);
    struct trap *trap = t_at(x, y);

    if (is_pet) {
        /* Pets avoid a trap if you've seen it usually. */
        if (trap && trap->tseen && rn2(40))
            return TRUE;
        /* Pets avoid cursed locations */
        if (cursed_object_at(x, y))
            return TRUE;

    /* Monsters avoid a trap if they've seen that type before */
    } else if (trap && rn2(40)
               && (mtmp->mtrapseen & (1 << (trap->ttyp - 1))) != 0) {
        return TRUE;
    }

    /* oversimplification:  creatures that bargethrough can't swap places
       when target monster is in rock or closed door or water (in particular,
       avoid moving to spots where mondied() won't leave a corpse; doesn't
       matter whether barger is capable of moving to such a target spot if
       it were unoccupied) */
    if (!accessible(x, y)
        /* mondied() allows is_pool() as an exception to !accessible(),
           but we'll only do that if 'mtmp' is already at a water location
           so that we don't swap a water critter onto land */
        && !(is_pool(x, y) && is_pool(mtmp->mx, mtmp->my)))
        return TRUE;

    return FALSE;
}

/*
 * Inventory prevents passage under door.
 * Used by can_ooze() and can_fog().
 */
STATIC_OVL boolean
stuff_prevents_passage(mtmp)
struct monst *mtmp;
{
    struct obj *chain, *obj;

    if (mtmp == &youmonst) {
        chain = invent;
    } else {
        chain = mtmp->minvent;
    }
    for (obj = chain; obj; obj = obj->nobj) {
        int typ = obj->otyp;

        if (typ == COIN_CLASS && obj->quan > 100L)
            return TRUE;
        if (obj->oclass != GEM_CLASS && !(typ >= ARROW && typ <= BOOMERANG)
            && !(typ >= DAGGER && typ <= CRYSKNIFE) && typ != SLING
            && !is_cloak(obj) && typ != FEDORA && !is_gloves(obj)
            && typ != LEATHER_JACKET && typ != CREDIT_CARD && !is_shirt(obj)
            && !(typ == CORPSE && verysmall(&mons[obj->corpsenm]))
            && typ != FORTUNE_COOKIE && typ != CANDY_BAR && typ != PANCAKE
            && typ != LEMBAS_WAFER && typ != LUMP_OF_ROYAL_JELLY
            && obj->oclass != AMULET_CLASS && obj->oclass != RING_CLASS
            && obj->oclass != VENOM_CLASS && typ != SACK
            && typ != BAG_OF_HOLDING && typ != BAG_OF_TRICKS
            && !Is_candle(obj) && typ != OILSKIN_SACK && typ != LEASH
            && typ != STETHOSCOPE && typ != BLINDFOLD && typ != TOWEL
            && typ != TIN_WHISTLE && typ != MAGIC_WHISTLE
            && typ != MAGIC_MARKER && typ != TIN_OPENER && typ != SKELETON_KEY
            && typ != LOCK_PICK)
            return TRUE;
        if (Is_container(obj) && obj->cobj)
            return TRUE;
    }
    return FALSE;
}

boolean
can_ooze(mtmp)
struct monst *mtmp;
{
    if (!amorphous(mtmp->data) || stuff_prevents_passage(mtmp))
        return FALSE;
    return TRUE;
}

/* monster can change form into a fog if necessary */
boolean
can_fog(mtmp)
struct monst *mtmp;
{
    if (!(mvitals[PM_FOG_CLOUD].mvflags & G_GENOD) && is_vampshifter(mtmp)
        && !Protection_from_shape_changers && !stuff_prevents_passage(mtmp))
        return TRUE;
    return FALSE;
}

STATIC_OVL int
vamp_shift(mon, ptr, domsg)
struct monst *mon;
struct permonst *ptr;
boolean domsg;
{
    int reslt = 0;
    char oldmtype[BUFSZ];

    /* remember current monster type before shapechange */
    Strcpy(oldmtype, domsg ? noname_monnam(mon, ARTICLE_THE) : "");

    if (mon->data == ptr) {
        /* already right shape */
        reslt = 1;
        domsg = FALSE;
    } else if (is_vampshifter(mon)) {
        reslt = newcham(mon, ptr, FALSE, FALSE);
    }

    if (reslt && domsg) {
        pline("You %s %s where %s was.",
              !canseemon(mon) ? "now detect" : "observe",
              noname_monnam(mon, ARTICLE_A), oldmtype);
        /* this message is given when it turns into a fog cloud
           in order to move under a closed door */
        display_nhwindow(WIN_MESSAGE, FALSE);
    }

    return reslt;
}

/*monmove.c*/
