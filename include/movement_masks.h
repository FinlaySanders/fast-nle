#ifndef NH_MOVEMENT_MASKS_H
#define NH_MOVEMENT_MASKS_H
struct nh_move_column { unsigned int nonrock, occupied; };

static inline void
nh_move_set_terrain(struct nh_move_column *cols, int x, int y, int nonrock)
{
    unsigned int bit = 1U << y;
    if (x && nonrock) cols[x + 1].nonrock |= bit;
    else cols[x + 1].nonrock &= ~bit;
}

static inline void
nh_move_set_occupied(struct nh_move_column *cols, int x, int y, int occupied)
{
    unsigned int bit = 1U << y;
    if (occupied) cols[x + 1].occupied |= bit;
    else cols[x + 1].occupied &= ~bit;
}

/* Bits follow the original x-major, then y-major traversal. */
static inline unsigned int
nh_move_neighbours(unsigned int left, unsigned int middle,
                   unsigned int right, int y)
{
    return ((((left << 1) >> y) & 7U)
            | ((((middle << 1) >> y) & 7U) << 3)
            | ((((right << 1) >> y) & 7U) << 6)) & 0x1efU;
}

static inline unsigned int
nh_move_valid(int x, int y)
{
    unsigned int rows = (1U << ROWNO) - 1U;
    return nh_move_neighbours(x > 1 ? rows : 0U,
                              x > 0 ? rows : 0U,
                              x + 1 < COLNO ? rows : 0U, y);
}

static inline unsigned int
nh_move_position_bit(int x, int y, int px, int py)
{
    unsigned int dx = (unsigned int) (px - x + 1);
    unsigned int dy = (unsigned int) (py - y + 1);
    return dx < 3 && dy < 3 ? 1U << (3 * dx + dy) : 0U;
}
#endif
