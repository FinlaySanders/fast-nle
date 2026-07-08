#!/usr/bin/env bash
# Oracle (a) from docs/DESIGN.md: prove libnethack has no mutable global state.
#
# Dumps the writable sections (.data/.bss/COMMON and TLS) of the built library
# and fails if any symbol is not in the whitelist. File-scope statics appear
# here as local symbols, so a missed global cannot hide.
#
# Three modes:
#   tools/check_no_globals.sh <libnethack.so|.dylib>          # strict CI gate
#   tools/check_no_globals.sh --inventory <lib>               # print every
#       writable symbol with size, sorted — this IS the migration worklist.
#   tools/check_no_globals.sh --ratchet <lib>                 # transitional
#       gate: fail only on symbols NOT in tools/global_baseline.txt (i.e. new
#       globals). The migration shrinks the baseline monotonically toward the
#       whitelist; regenerate it with --inventory | cut -f1 after each sweep.
#
# Whitelist: tools/global_whitelist.txt, one symbol per line, '#' comments.
# Every entry must carry a justification comment. Expected steady state:
# the single TLS ctx pointer + const-in-practice tables upstream forgot to
# mark const (each to be fixed or justified).
#
# Symbol names are normalized (leading Mach-O underscore stripped) so the
# baseline/whitelist are portable between macOS dev boxes and Linux CI.
set -euo pipefail

mode=check
case "${1:-}" in
--inventory) mode=inventory; shift ;;
--ratchet) mode=ratchet; shift ;;
esac
lib="${1:?usage: check_no_globals.sh [--inventory|--ratchet] <library>}"
whitelist="$(dirname "$0")/global_whitelist.txt"
baseline="$(dirname "$0")/global_baseline.txt"

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
        # ltmpN are assembler section-start labels, not real symbols
        nm -m "$lib" 2>/dev/null \
            | awk '$2 ~ /^\(__DATA[^,]*,__(data|bss|common)\)$/ \
                   && $NF !~ /^ltmp[0-9]+$/ \
                   { sym = $NF; sub(/^_/, "", sym);
                     print sym "\t0\t" substr($2, 2, length($2)-2) }' \
            | sort -u
        ;;
    *)
        # ELF: nm can't distinguish .data.rel.ro (const-with-relocations,
        # remapped READ-ONLY after dynamic linking) from real .data — both
        # print as D/d. Use objdump's section column and keep only genuine
        # writable sections.
        objdump -t "$lib" 2>/dev/null \
            | awk '$4 == ".data" || $4 == ".bss" || $4 == "*COM*" \
                   { print $NF "\t" $(NF-1) "\t" $4 }' \
            | grep -vE '^(\.data|\.bss|completed\.[0-9]+)\t' \
            | sort -u
        ;;
    esac
}

if [ "$mode" = inventory ]; then
    # Largest first: the worklist for globals.def
    list_writable | sort -t$'\t' -k2 -r
    exit 0
fi

allowed=$(mktemp)
trap 'rm -f "$allowed"' EXIT
if [ -f "$whitelist" ]; then
    grep -v '^#' "$whitelist" | sed 's/[[:space:]].*//' | grep -v '^$' >> "$allowed" || true
fi
if [ "$mode" = ratchet ]; then
    if [ ! -f "$baseline" ]; then
        echo "ratchet mode needs $baseline (generate: --inventory | cut -f1)" >&2
        exit 2
    fi
    grep -v '^#' "$baseline" | sed 's/[[:space:]].*//' | grep -v '^$' >> "$allowed" || true
fi

fails=0
count=0
while IFS=$'\t' read -r sym size type; do
    [ -z "$sym" ] && continue
    count=$((count + 1))
    if grep -qxF "$sym" "$allowed"; then
        continue
    fi
    echo "MUTABLE GLOBAL NOT ALLOWED: $sym (size $size, type $type)" >&2
    fails=$((fails + 1))
done < <(list_writable)

if [ "$fails" -gt 0 ]; then
    if [ "$mode" = ratchet ]; then
        echo "FAIL: $fails NEW writable symbol(s) vs baseline in $lib" >&2
        echo "New per-process state would be shared across all envs." >&2
    else
        echo "FAIL: $fails non-whitelisted writable symbol(s) in $lib" >&2
        echo "Each is per-process state that will be shared across all envs." >&2
    fi
    exit 1
fi
if [ "$mode" = ratchet ]; then
    echo "OK (ratchet): no new mutable globals; $count remain vs baseline of $(grep -cv '^#' "$baseline") — shrink toward whitelist"
else
    echo "OK: no mutable globals outside whitelist in $lib"
fi
