#!/usr/bin/env bash
# Oracle (a) from docs/DESIGN.md: prove libnethack has no mutable global state.
#
# Dumps the writable sections (.data/.bss/COMMON and TLS) of the built library
# and fails if any symbol is not in the whitelist. File-scope statics appear
# here as local symbols, so a missed global cannot hide.
#
# Two modes:
#   tools/check_no_globals.sh <libnethack.so|.dylib>              # CI gate
#   tools/check_no_globals.sh --inventory <lib>                   # print every
#       writable symbol with size, sorted — this IS the migration worklist.
#
# Whitelist: tools/global_whitelist.txt, one symbol per line, '#' comments.
# Every entry must carry a justification comment. Expected steady state:
# the single TLS ctx pointer + const-in-practice tables upstream forgot to
# mark const (each to be fixed or justified).
set -euo pipefail

mode=check
if [ "${1:-}" = "--inventory" ]; then mode=inventory; shift; fi
lib="${1:?usage: check_no_globals.sh [--inventory] <library>}"
whitelist="$(dirname "$0")/global_whitelist.txt"

# ELF: nm type codes are reliable — D/d = .data, B/b = .bss, C/c = common
# (upper = global, lower = local/static). TLS lands in .tdata/.tbss.
# Mach-O (macOS dev boxes): zero-init globals live in __DATA,__common and nm
# reports them as 'S'/'s', which also covers read-only __TEXT sections — type
# letters are NOT sufficient. Filter by writable __DATA segment via `nm -m`.
list_writable() {
    case "$(uname -s)" in
    Darwin)
        # nm -m: "<addr> (__SEG,__sect) [external] _name"
        # Writable = __DATA/__DATA_DIRTY data|bss|common (NOT __const).
        nm -m "$lib" 2>/dev/null \
            | awk '$2 ~ /^\(__DATA[^,]*,__(data|bss|common)\)$/ \
                   { print $NF "\t0\t" substr($2, 2, length($2)-2) }' \
            | sort -u
        ;;
    *)
        if command -v llvm-nm >/dev/null 2>&1; then NM=llvm-nm; else NM=nm; fi
        # --no-demangle keeps C++ symbols greppable against the whitelist
        $NM --print-size --no-demangle "$lib" 2>/dev/null \
            | awk 'NF >= 4 && $3 ~ /^[DdBbCc]$/ { print $4 "\t" $2 "\t" $3 }' \
            | sort -u
        ;;
    esac
}

if [ "$mode" = inventory ]; then
    # Largest first: the worklist for globals.def
    list_writable | sort -t$'\t' -k2 -r
    exit 0
fi

fails=0
while IFS=$'\t' read -r sym size type; do
    [ -z "$sym" ] && continue
    if [ -f "$whitelist" ] && grep -qxF "$sym" <(grep -v '^#' "$whitelist" | sed 's/[[:space:]].*//'); then
        continue
    fi
    echo "MUTABLE GLOBAL NOT WHITELISTED: $sym (size $size, type $type)" >&2
    fails=$((fails + 1))
done < <(list_writable)

if [ "$fails" -gt 0 ]; then
    echo "FAIL: $fails non-whitelisted writable symbol(s) in $lib" >&2
    echo "Each is per-process state that will be shared across all envs." >&2
    exit 1
fi
echo "OK: no mutable globals outside whitelist in $lib"
