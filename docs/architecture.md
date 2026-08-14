# Architecture

NetAudit is organized into independent layers so that logic can be tested
and reused outside of the CLI:

- **`commands/`** — Typer command functions. Parse args, call into the
  layers below, format output. No business logic lives here.
- **`scanner/`** — low-level network probing: ICMP (`icmp.py`, via the
  system `ping` binary), TCP connect scanning (`tcp.py`), ARP/MAC discovery
  (`arp.py`, via Scapy), and host discovery orchestration (`discovery.py`).
- **`network/`** — DNS (`dns.py`, via dnspython), traceroute (`routing.py`,
  via the system `traceroute`/`tracert` binary), local interfaces
  (`interfaces.py`, via psutil), and HTTP(S) checks (`latency.py`, via httpx).
- **`devices/`** — Netmiko connection handling (`connector.py`) and
  per-vendor read-only command sets (`cisco.py`, `juniper.py`, `arista.py`,
  `generic.py`).
- **`diagnostics/`** — individual check functions (`checks.py`), Cisco IOS
  output parsers (`interfaces.py`, `services.py`), and the `doctor` scoring
  engine (`health.py`).
- **`snapshots/`** — snapshot capture/storage (`manager.py`) and diffing
  (`differ.py`).
- **`reports/`** — JSON/CSV/Markdown/HTML report generation.
- **`config/`** — YAML + environment-variable settings via
  pydantic-settings.
- **`utils/`** — logging, input validation, Rich console instances, and
  dependency-free helper data (service-name table, JSON serialization).

## A command's lifecycle

1. Typer parses CLI args and calls the command function.
2. The command validates input (`utils.validators`) and returns a clean
   exit code on failure (see `docs/exit-codes.md`).
3. The command calls into `scanner`/`network`/`devices`/`diagnostics` to do
   the actual work, and never talks to the network directly itself.
4. Results are formatted for either a Rich table (interactive) or plain
   JSON/CSV (`--json`/`--csv`, for automation).
