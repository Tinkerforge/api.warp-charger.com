#!/bin/sh
# Simple auto-deploy from github
# This is called on the api server with cron (as root).
# Git operations run as user api, service restart as root.

set -e

BRANCH="master"

cd /home/api/api.warp-charger.com
su -s /bin/sh api -c "/usr/bin/git fetch origin $BRANCH"

LOCAL_HASH=$(su -s /bin/sh api -c "/usr/bin/git rev-parse HEAD")
REMOTE_HASH=$(su -s /bin/sh api -c "/usr/bin/git rev-parse origin/$BRANCH")

# Exit silently if nothing changed
[ "$LOCAL_HASH" = "$REMOTE_HASH" ] && exit 0

su -s /bin/sh api -c "/usr/bin/git reset --hard origin/$BRANCH"
/usr/bin/systemctl restart api.warp-charger.com
