#!/bin/bash
# run_path.sh <chd> <prefix> [shots] : boot, char select, mode select, challenge mission (mashed), results, route select
T=$(cd "$(dirname "$0")" && pwd); E=${VF4FT_TEST:-$T/work}; mkdir -p "$E"; cd "$E"
"$T/ra.sh" stop >/dev/null 2>&1
mkdir -p roms/vf4tuned; ln -sf "$(realpath "$1")" roms/vf4tuned/gds-0036f.chd
"$T/ra.sh" start >/dev/null; sleep 55
"$T/ra.sh" key Return 600; sleep 6; "$T/ra.sh" key Return 600; sleep 10
"$T/ra.sh" shot $2_char >/dev/null
"$T/ra.sh" key x 300; sleep 12; "$T/ra.sh" shot $2_mode >/dev/null
"$T/ra.sh" key Right 300; sleep 2; "$T/ra.sh" key x 300; sleep 10
"$T/ra.sh" shot $2_intro >/dev/null; sleep 18; "$T/ra.sh" shot $2_hud >/dev/null
export DISPLAY=:99; end=$((SECONDS+140))
while [ $SECONDS -lt $end ]; do xdotool keydown Right; xdotool key --delay 60 x x z x z; xdotool keyup Right; xdotool key --delay 60 x x x z; done
for i in $(seq -w 1 ${3:-16}); do sleep 4; "$T/ra.sh" shot $2_p$i >/dev/null; done
