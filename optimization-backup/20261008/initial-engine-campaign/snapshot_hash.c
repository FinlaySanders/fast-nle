#include <stdint.h>
#include <stddef.h>
uint64_t snapshot_fnv(uint64_t hash, const unsigned char* bytes, size_t size) {
    for (size_t i = 0; i < size; ++i) hash = (hash ^ bytes[i]) * UINT64_C(1099511628211);
    return hash;
}
