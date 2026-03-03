#!/usr/bin/env bash

########################################
#  Environment configuration
########################################

# Detect root (GitHub Actions vs devcontainer/local)
if [[ -n "${GITHUB_WORKSPACE:-}" ]]; then
  ROOT="$GITHUB_WORKSPACE"
else
  ROOT="/workspace"
fi

PLAYLIST="$ROOT/OpenIPTVItaly.m3u"
REPORT="$ROOT/health_report.txt"

SKIP_REGEX="(Teledue)"
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64; IPTV-Health-Check)"

echo "Environment root: $ROOT"
echo "Playlist:         $PLAYLIST"
echo "Report:           $REPORT"
echo ""

########################################
#  Check playlist
########################################

if [[ ! -f "$PLAYLIST" ]]; then
  echo "ERROR: Playlist not found: $PLAYLIST"
  exit 1
fi

########################################
#  Normalize playlist (CRLF + BOM)
########################################

sed -i 's/\r$//' "$PLAYLIST" || true
sed -i '1s/^\xEF\xBB\xBF//' "$PLAYLIST" || true

########################################
#  Initialize report
########################################

{
  echo "IPTV Health Dashboard"
  echo "Generated: $(date -u)"
  echo ""
} > "$REPORT"

TOTAL=0
WORKING=0
DOWN=0
SKIPPED=0
CURRENT_CHANNEL=""
URL_PROCESSED=false

########################################
#  ffmpeg test functions
########################################

check_stream() {
    local url="$1"

    # Special headers for Mediaset MPD
    if [[ "$url" == *mediaset* || "$url" == *.mpd ]]; then
        ffmpeg -v error \
            -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36" \
            -headers "Referer: https://www.mediasetplay.mediaset.it/" \
            -headers "Origin: https://www.mediasetplay.mediaset.it" \
            -headers "Accept-Language: it-IT,it;q=0.9" \
            -protocol_whitelist file,http,https,tcp,tls \
            -timeout 5000000 \
            -rw_timeout 5000000 \
            -stimeout 5000000 \
            -i "$url" \
            -map 0:v:0 \
            -t 1 \
            -f null - \
            </dev/null >/dev/null 2>&1
        return $?
    fi

    # Normal ffmpeg for all other channels
    ffmpeg -v error \
        -user_agent "$USER_AGENT" \
        -protocol_whitelist file,http,https,tcp,tls \
        -timeout 5000000 \
        -rw_timeout 5000000 \
        -stimeout 5000000 \
        -i "$url" \
        -map 0:v:0 \
        -t 1 \
        -f null - \
        </dev/null >/dev/null 2>&1

    return $?
}

########################################
#  Playlist loop
########################################

while IFS= read -r LINE; do

  # New channel
  if [[ "$LINE" == \#EXTINF* ]]; then
    CURRENT_CHANNEL=$(echo "$LINE" | sed 's/.*,//')
    URL_PROCESSED=false
    continue
  fi

  # Skip metadata lines (#EXTSIZE, #EXTVLCOPT, etc.)
  if [[ "$LINE" == \#EXT* ]]; then
    continue
  fi

  # URL line
  if [[ "$LINE" == http* ]]; then

    # Only process the FIRST URL after #EXTINF
    if [[ "$URL_PROCESSED" == true ]]; then
        continue
    fi
    URL_PROCESSED=true

    URL="$LINE"

    # Skip channels
    if [[ "$CURRENT_CHANNEL" =~ $SKIP_REGEX ]]; then
      echo "[SKIP]  $CURRENT_CHANNEL" >> "$REPORT"
      ((SKIPPED++))
      continue
    fi

    ((TOTAL++))
    START=$(date +%s%3N)

    if check_stream "$URL"; then
        END=$(date +%s%3N)
        TIME_MS=$((END - START))
        echo "[OK]    $CURRENT_CHANNEL | ${TIME_MS}ms" >> "$REPORT"
        ((WORKING++))
    else
        echo "[DOWN]  $CURRENT_CHANNEL" >> "$REPORT"
        ((DOWN++))
    fi
  fi

done < "$PLAYLIST"

########################################
#  Final summary
########################################

{
  echo ""
  echo "Total tested: $TOTAL"
  echo "Working:      $WORKING"
  echo "Down:         $DOWN"
  echo "Skipped:      $SKIPPED"
} >> "$REPORT"

echo "Report generated at: $REPORT"