#!/usr/bin/with-contenv bash

echo "Starting Script...."
# Clear stale Deemix API polling helpers from previous interrupted runs.
pkill -9 -f "/config/scripts/deemix_api_download.bash" 2>/dev/null || true
pkill -9 -f "/scripts/deemix_api_download.bash" 2>/dev/null || true
pkill -9 -f "deemix_api_download.bash" 2>/dev/null || true

processstartid="$(ps -A -o pid,cmd|grep "/config/scripts/start.bash" | grep -v grep | head -n 1 | awk '{print $1}')"
echo "To kill script, use the following command:"
echo "kill -9 $processstartid"
for (( ; ; )); do
	let i++
	# MusicBrainz is optional. Deezer/Bambanah is the default AMA workflow.
	# Explicit MUSICBRAINZ_ENABLED overrides the legacy /config/run_alternate marker.
	if [ -z "${MUSICBRAINZ_ENABLED+x}" ]; then
		if [ -f /config/run_alternate ]; then
			MUSICBRAINZ_ENABLED=true
			echo "WARNING: Legacy /config/run_alternate detected; use MUSICBRAINZ_ENABLED=true instead."
		else
			MUSICBRAINZ_ENABLED=false
		fi
	fi

	case "$(printf "%s" "$MUSICBRAINZ_ENABLED" | tr "[:upper:]" "[:lower:]")" in
		true|1|yes|on)
			echo "MusicBrainz: ENABLED"
			bash /config/scripts/download_musicbrainz.bash 2>&1 | tee "/config/logs/script_run_${i}_$(date +"%Y_%m_%d_%I_%M_%p").log" > /proc/1/fd/1 2>/proc/1/fd/2
			;;
		*)
			echo "MusicBrainz: DISABLED"
			bash /config/scripts/download.bash 2>&1 | tee "/config/logs/script_run_${i}_$(date +"%Y_%m_%d_%I_%M_%p").log" > /proc/1/fd/1 2>/proc/1/fd/2
			;;
	esac
	if [ -f "/config/logs/log-cleanup" ]; then
		rm "/config/logs/log-cleanup"
	fi
	touch -d "8 hours ago" "/config/logs/log-cleanup"
	if find "/config/logs" -type f -iname "*.log" -not -newer "/config/logs/log-cleanup" | read; then
		find "/config/logs" -type f -iname "*.log" -not -newer "/config/logs/log-cleanup" -delete
	fi
	if [ -f "/config/logs/log-cleanup" ]; then
		rm "/config/logs/log-cleanup"
	fi
	if [ -z "$SCRIPTINTERVAL" ]; then
		SCRIPTINTERVAL="15m"
	fi
	sleep $SCRIPTINTERVAL
done

exit 0
