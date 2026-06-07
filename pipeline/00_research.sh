#!/usr/bin/env bash
# Stage 0: Topic research via last30days (optional pre-pipeline).
#
# Generates notes.md from a topic using the last30days research skill
# (https://github.com/mvanhorn/last30days-skill). If notes.md already
# exists in the current build directory, this stage is a no-op.
#
# Two ways to satisfy this stage:
#
#   1. AUTOMATED: install last30days CLI:
#        pip install last30days
#        last30days "<topic>" --output notes.md
#      Then re-run this script (it will detect notes.md and skip).
#
#   2. MANUAL: invoke the last30days Claude Code skill in your
#      Claude Code session:
#        /last30days <topic>
#      Claude will write notes.md for you. Then re-run.
#
#   3. BYPASS: write notes.md by hand. Just needs ≥5 lines of
#      facts/sources for the topic. Then re-run.
#
# Usage:
#   00_research.sh <topic> [<output_file>]
#
# Exit codes:
#   0  notes.md exists with content — proceed to Stage 1
#   1  notes.md missing or empty — needs research first
#   2  CLI tool not installed, instructions printed

set -euo pipefail

TOPIC="${1:?usage: $0 <topic> [output_file]}"
OUT="${2:-$(pwd)/notes.md}"

# Already have notes? Skip.
if [ -f "$OUT" ] && [ -s "$OUT" ]; then
    lines=$(wc -l < "$OUT")
    echo "✓ $OUT already exists ($lines lines, $(wc -c < "$OUT") bytes) — skipping Stage 0"
    exit 0
fi

echo "📝 Stage 0: Research needed for topic: \"$TOPIC\""
echo "   output target: $OUT"
echo ""

# Try the last30days CLI first
if command -v last30days >/dev/null 2>&1; then
    echo "  → Running last30days CLI..."
    last30days "$TOPIC" --output "$OUT"
    echo "  ✓ notes.md written"
    exit 0
fi

# Try alternative binary names
for bin in l30d last-30-days; do
    if command -v "$bin" >/dev/null 2>&1; then
        echo "  → Running $bin CLI..."
        "$bin" "$TOPIC" --output "$OUT"
        echo "  ✓ notes.md written"
        exit 0
    fi
done

# No CLI — print instructions
echo "  ✗ last30days CLI not installed (and notes.md missing)"
echo ""
echo "  To satisfy Stage 0, choose ONE of:"
echo ""
echo "  A) Install last30days CLI (fastest):"
echo "       pip install last30days"
echo "       last30days \"$TOPIC\" --output $OUT"
echo ""
echo "  B) Use the Claude Code /last30days skill (interactive):"
echo "       In Claude Code, run:  /last30days $TOPIC"
echo "       Save the output to:    $OUT"
echo ""
echo "  C) Write notes.md by hand (≥5 lines of facts + sources)"
echo ""
echo "  Then re-run:  ./run_all.sh <narration.md>"
exit 2
