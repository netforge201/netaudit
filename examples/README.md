# Examples

A few common NetAudit workflows.

## Discover your LAN and check for open management ports

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443,3389 --json > scan.json
netaudit report scan.json --format html
open reports/scan.html   # or: xdg-open reports/scan.html
```

## Health-check a router, including device-level checks

```bash
export NETAUDIT_USERNAME=admin
export NETAUDIT_PASSWORD=changeme   # or omit and let NetAudit prompt

netaudit doctor 192.168.1.1 --device --device-type cisco_ios
```

## Track a switch's interface state over time

```bash
# Run this daily (e.g. via cron)
netaudit snapshot 192.168.1.10 --device-type cisco_ios

# See what changed since yesterday
netaudit diff 192.168.1.10
```

## Pipe results into other tools

```bash
# Every host that's up, as a plain IP list
netaudit scan 192.168.1.0/24 --json | jq -r '.hosts[] | select(.status=="up") | .ip'

# Open ports as CSV for a spreadsheet
netaudit ports 192.168.1.1 --range 1-1024 --csv > ports.csv
```
