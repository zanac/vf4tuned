#!/bin/bash
# Headless RetroArch + Flycast test driver.
# Work dir ($VF4FT_TEST, default test/work) must contain: flycast_libretro.so, system/dc/naomi2.zip,
# roms/vf4tuned.zip, roms/vf4tuned/gds-0036f.chd (run_path.sh links it).
#   ra.sh start            start Xvfb + RetroArch with VF4 FT (log in ra.log)
#   ra.sh key <key> [ms]   hold a key (xdotool name) for ms (default 300)
#   ra.sh shot <name>      RetroArch screenshot -> shots/<name>.png
#   ra.sh stop
E=${VF4FT_TEST:-$(cd "$(dirname "$0")" && pwd)/work}
export DISPLAY=:99
case "$1" in
start)
  pkill -9 -x Xvfb; rm -f /tmp/.X99-lock; sleep 1; Xvfb :99 -screen 0 800x600x24 >/dev/null 2>&1 & sleep 2
  mkdir -p "$E/cfg" "$E/shots" "$E/saves" "$E/states"
  sed "s#@E@#$E#g" "$(dirname "$0")/retroarch.cfg" > "$E/cfg/retroarch.cfg"
  cp "$(dirname "$0")/core.opt" "$E/cfg/core.opt"
  export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe LP_NUM_THREADS=2
  nohup dbus-run-session -- retroarch -L "${CORE:-$E/flycast_libretro.so}" -c "$E/cfg/retroarch.cfg" "$E/roms/vf4tuned.zip" >"$E/ra.log" 2>&1 &
  sleep 5; pgrep -a retroarch | head -1
  ;;
key)
  W=$(xdotool search --onlyvisible --class retroarch | head -1)
  [ -n "$W" ] && xdotool windowfocus --sync "$W" 2>/dev/null
  xdotool keydown "$2"; sleep "$(awk "BEGIN{print ${3:-300}/1000}")"; xdotool keyup "$2"
  ;;
shot)
  before=$(ls -t "$E/shots" 2>/dev/null | head -1)
  python3 -c "import socket;s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.sendto(b'SCREENSHOT',('127.0.0.1',55355))"
  for i in $(seq 1 60); do sleep 1; n=$(ls -t "$E/shots" | head -1); [ -n "$n" ] && [ "$n" != "$before" ] && break; done
  sleep 1; mv "$E/shots/$n" "$E/shots/$2.png" && echo "$E/shots/$2.png"
  ;;
stop)
  pkill -9 retroarch; pkill -9 -f dbus-run-session; pkill -9 Xvfb; sleep 1
  ;;
esac
