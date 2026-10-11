#ifndef NH_MOVEMENT_FACTS_H
#define NH_MOVEMENT_FACTS_H
#define NH_SUMMARY(x, y) (nh_move_summary[(x)][(y)])
#define NH_MOVE_TERRAIN 1U
#define NH_MOVE_PILES   2U
#define NH_MOVE_TRAPS   4U
#define NH_MOVE_GAS     8U
#define NH_MOVE_ALL     15U
#define MV_ROCK        (1U << 0)
#define MV_TREE        (1U << 1)
#define MV_PASSWALL    (1U << 2)
#define MV_DIG         (1U << 3)
#define MV_BARS        (1U << 4)
#define MV_NONDIG      (1U << 5)
#define MV_DOOR        (1U << 6)
#define MV_CLOSED      (1U << 7)
#define MV_LOCKED      (1U << 8)
#define MV_DOOR_DIAG   (1U << 9)
#define MV_POOL        (1U << 10)
#define MV_LAVA        (1U << 11)
#define MV_ALTAR       (1U << 12)
#define MV_BOULDER     (1U << 13)
#define MV_GARLIC      (1U << 14)
#define MV_SCARE       (1U << 15)
#define MV_TRAP_SHIFT  16
#define MV_TRAP_TYPE   (31U << MV_TRAP_SHIFT)
#define MV_TRAP        (1U << 21)
#define MV_GAS         (1U << 22)
#define MV_TERRAIN_MASK ((1U << 13) - 1)
#define MV_PILE_MASK   (MV_BOULDER | MV_GARLIC | MV_SCARE)
#define MV_TRAP_MASK   (MV_TRAP | MV_TRAP_TYPE)

extern void nh_pile_update(int, int);
extern void nh_trap_update(int, int);
extern void nh_tile_clear_entities(unsigned int);
#define NH_PILE_WRITE(obj, expr) \
    ({ int nh_result_ = (expr); \
       if ((obj)->where == OBJ_FLOOR) nh_pile_update((obj)->ox, (obj)->oy); \
       nh_result_; })
#define NH_TRAP_WRITE(trap, expr) \
    ({ int nh_result_ = (expr); nh_trap_update((trap)->tx, (trap)->ty); nh_result_; })
#endif
