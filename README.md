# NetAudit

<p align="center">
  <strong>Network Audit & Diagnostics Toolkit</strong><br>
  A practical CLI for network discovery, diagnostics and infrastructure visibility.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#network-discovery">Network Discovery</a> •
  <a href="#commands">Commands</a> •
  <a href="#development">Development</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-111111?style=for-the-badge" alt="Platform">
  <img src="https://img.shields.io/badge/Interface-CLI-orange?style=for-the-badge" alt="CLI">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT">
  <img src="https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge" alt="Beta">
</p>

---

## Overview

**NetAudit** is a command-line network auditing and diagnostics toolkit written in Python.

It is designed for network engineers, system administrators, infrastructure engineers, cybersecurity students, IT support engineers and developers working with network infrastructure.

NetAudit provides practical network visibility directly from the terminal.

It can discover hosts, identify MAC addresses and vendors, resolve hostnames, inspect ports, test connectivity, query DNS, trace routes, inspect local interfaces, communicate with supported network devices and generate reports.

The project follows a simple principle:

> Report what was actually observed. Never fabricate network information.

---

## Features

### Network discovery

- CIDR network scanning
- Concurrent host discovery
- ICMP reachability detection
- Latency measurement
- MAC address discovery
- ARP table integration
- macOS `arp` integration
- Linux neighbor-table integration
- Optional Scapy ARP fallback
- MAC address normalization
- Vendor identification
- OUI-based vendor fallback
- `manuf` database vendor lookup
- Reverse DNS hostname resolution
- `/etc/hosts` hostname resolution
- macOS SMB / NetBIOS hostname discovery
- macOS Bonjour / mDNS support
- TCP service discovery
- Optional port scanning during network discovery

### Diagnostics

- ICMP ping
- Packet loss
- Latency
- TTL information
- Best-effort OS family hints
- DNS lookups
- Reverse DNS
- Route tracing
- Local interface inspection
- TCP port scanning
- HTTP/HTTPS checks
- Network health diagnostics

### Network devices

- Cisco IOS / IOS-XE
- Cisco NX-OS
- Cisco IOS-XR
- Juniper Junos
- Arista EOS
- Generic network devices
- SSH connectivity through Netmiko
- Read-only device commands
- Device snapshots
- Snapshot comparison

### Output

- Human-readable terminal tables
- JSON
- CSV
- Markdown
- HTML reports

### Development

- Pytest test suite
- Ruff linting
- Mypy support
- GitHub Actions
- Modular scanner architecture

---

# Network Discovery

The main network discovery command is:

```bash
netaudit scan 192.168.1.0/24
```

The scanner combines several mechanisms rather than depending on one protocol.

A typical result can contain:

```text
IP              STATUS  LATENCY  HOSTNAME       MAC                  VENDOR
10.0.0.1        UP      5.2 ms   router         00:11:22:33:44:55   ExampleVendor
10.0.0.20       UP      0.8 ms   workstation    AA:BB:CC:DD:EE:FF   Apple
10.0.0.30       UP      0.7 ms   —              12:34:56:78:9A:BC   —
```

The values above are synthetic examples and do not represent a real network.

Not every device will expose every field.

For example, a device may:

- respond to ICMP but not expose a hostname;
- have a MAC address but no recognizable vendor;
- expose a hostname through SMB but not reverse DNS;
- block ICMP while still exposing TCP services.

NetAudit keeps these results separate instead of treating missing information as failure.

---

## MAC Address Discovery

On macOS, NetAudit first uses the system ARP table.

For example:

```bash
arp -an
```

Entries such as:

```text
? (10.0.0.1) at 00:11:22:33:44:55 on en0
```

are normalized to:

```text
00:11:22:33:44:55
```

This is important because macOS may display some hexadecimal MAC octets using a single digit.

Scapy is available as a fallback for environments where raw ARP access is possible.

Raw packet access may require elevated privileges depending on the operating system.

---

## Vendor Identification

NetAudit uses multiple methods to identify the manufacturer of a MAC address.

The preferred lookup uses the `manuf` database when available.

Example:

```text
00:11:22:33:44:55 -> ExampleVendor
AA:BB:CC:DD:EE:FF -> ExampleVendor
12:34:56:78:9A:BC -> ExampleVendor
```

A built-in OUI fallback is also available for common vendors.

Vendor detection is best-effort.

A result of:

```text
VENDOR: —
```

does not mean that the MAC address is invalid. It means that no matching vendor was available from the installed databases or fallback table.

---

# Hostname Discovery

Hostname resolution uses several mechanisms.

### 1. SMB / NetBIOS on macOS

For devices exposing SMB, NetAudit can use:

```bash
smbutil status <IP>
```

For example:

```text
Using IP address of 10.0.0.20: 10.0.0.20
Workgroup: WORKGROUP
Server: EXAMPLE-WORKSTATION
```

NetAudit can extract:

```text
EXAMPLE-WORKSTATION
```

as the hostname.

### 2. Reverse DNS

The scanner attempts:

```python
socket.gethostbyaddr(ip)
```

If a PTR record exists, the hostname is returned.

### 3. `/etc/hosts`

Local hostname mappings are checked as another fallback.

### 4. macOS Bonjour / mDNS

On macOS, NetAudit can use:

```bash
dns-sd
```

for local Bonjour-related discovery.

Bonjour resolution is intentionally best-effort because some `dns-sd` operations can remain active while waiting for network responses.

NetAudit applies strict timeouts and avoids blocking the entire network scan on a single Bonjour lookup.

---

# Installation

## Requirements

- Python 3.11+
- macOS or Linux
- Windows support is best-effort

The project uses:

- Typer
- Rich
- Scapy
- Netmiko
- Pydantic
- Pydantic Settings
- PyYAML
- HTTPX
- dnspython
- psutil
- python-dotenv

Development dependencies include:

- pytest
- pytest-cov
- Ruff
- Mypy

---

## Quick Install

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
./install.sh
```

The installer can use `pipx` when available or create a local virtual environment.

---

## Manual Installation

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

---

# Quick Start

## Scan a local network

```bash
netaudit scan 192.168.1.0/24
```

Scan a smaller network:

```bash
netaudit scan 192.168.1.0/28
```

Use more workers:

```bash
netaudit scan 192.168.1.0/24 --workers 100
```

Change the timeout:

```bash
netaudit scan 192.168.1.0/24 --timeout 0.5
```

Scan hosts and selected TCP ports:

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443,445
```

Export JSON:

```bash
netaudit scan 192.168.1.0/24 --json > scan.json
```

Export CSV:

```bash
netaudit scan 192.168.1.0/24 --csv > scan.csv
```

---

# Commands

## `scan`

Discover hosts in a CIDR range.

```bash
netaudit scan 192.168.1.0/24
```

With ports:

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443,445
```

JSON:

```bash
netaudit scan 192.168.1.0/24 --json
```

CSV:

```bash
netaudit scan 192.168.1.0/24 --csv
```

Common options:

| Option | Description |
|---|---|
| `--timeout` | Per-host timeout |
| `--workers` | Concurrent worker count |
| `--ports` | TCP ports to check |
| `--json` | JSON output |
| `--csv` | CSV output |
| `--quiet` | Reduce terminal output |

NetAudit limits CIDR scanning to 65,536 addresses to prevent accidental large-scale scans.

---

## `host`

Inspect an individual host:

```bash
netaudit host 192.168.1.1
```

Depending on the target, information can include:

- IP address
- Reachability
- Latency
- TTL
- OS family hint
- Hostname
- MAC address
- Vendor
- Open ports
- Services

---

## `ports`

Scan TCP ports:

```bash
netaudit ports 192.168.1.1
```

Selected ports:

```bash
netaudit ports 192.168.1.1 --ports 22,80,443
```

Port range:

```bash
netaudit ports 192.168.1.1 --range 1-1024
```

NetAudit performs connectivity checks and service identification.

It does not attempt to exploit discovered services.

---

## `ping`

Test reachability and latency:

```bash
netaudit ping 8.8.8.8
```

Multiple packets:

```bash
netaudit ping 8.8.8.8 --count 10
```

---

## `dns`

Forward lookup:

```bash
netaudit dns example.com
```

Reverse lookup:

```bash
netaudit dns 8.8.8.8 --reverse
```

Supported record types include:

```text
A
AAAA
MX
NS
TXT
CNAME
PTR
```

---

## `route`

Trace the route to a destination:

```bash
netaudit route 8.8.8.8
```

---

## `interfaces`

Inspect local network interfaces:

```bash
netaudit interfaces
```

Depending on the platform, output can include:

- Interface name
- Interface state
- MAC address
- IPv4 addresses
- IPv6 addresses
- MTU
- RX statistics
- TX statistics

---

## `doctor`

Run network diagnostics:

```bash
netaudit doctor 192.168.1.1
```

For a network device:

```bash
netaudit doctor 192.168.1.1 \
  --device \
  --device-type cisco_ios
```

Depending on the target, diagnostics can include:

- ICMP
- Packet loss
- Latency
- DNS
- HTTP/HTTPS
- TCP services
- SSH
- Interface state
- Interface errors
- Uptime
- Default route
- ARP
- NTP
- BGP
- OSPF

Unavailable checks are reported as unavailable rather than guessed.

---

# Network Devices

NetAudit supports read-only access to network infrastructure through Netmiko.

| Platform | Device type |
|---|---|
| Cisco IOS / IOS-XE | `cisco_ios` |
| Cisco NX-OS | `cisco_nxos` |
| Cisco IOS-XR | `cisco_xr` |
| Juniper Junos | `juniper_junos` |
| Arista EOS | `arista_eos` |
| Generic | `generic` |

Example:

```bash
netaudit device info 192.168.1.1 \
  --device-type cisco_ios
```

Connect:

```bash
netaudit device connect 192.168.1.1 \
  --device-type cisco_ios
```

Device operations are intended to be read-only.

---

# Snapshots

Create a device snapshot:

```bash
netaudit snapshot 192.168.1.1 \
  --device-type cisco_ios
```

List snapshots:

```bash
netaudit snapshot --list
```

Compare snapshots:

```bash
netaudit diff 192.168.1.1
```

Snapshots can be used to identify configuration or operational state changes over time.

---

# Reports

Generate HTML:

```bash
netaudit report scan.json --format html
```

Generate Markdown:

```bash
netaudit report scan.json \
  --format markdown \
  --output report.md
```

Supported formats:

```text
JSON
CSV
Markdown
HTML
```

---

# Configuration

Initialize configuration:

```bash
netaudit config init
```

Show configuration:

```bash
netaudit config show
```

Default configuration:

```text
~/.netaudit/config.yaml
```

Example:

```yaml
defaults:
  timeout: 2
  workers: 50

scanner:
  default_ports:
    - 22
    - 80
    - 443
    - 445

reports:
  directory: ./reports

snapshots:
  directory: ./snapshots
```

Environment variables can also be used for configuration.

---

# Credentials

Network-device credentials should never be committed to Git.

Credential sources can include:

1. CLI options
2. Environment variables
3. Interactive hidden password input

Example:

```bash
export NETAUDIT_USERNAME="admin"
export NETAUDIT_PASSWORD="your-password"
```

Do not commit real credentials to:

- Git repositories
- README files
- configuration files
- screenshots
- issue reports
- shell history

---

# Architecture

```text
netaudit/
├── cli.py
├── commands/
│   ├── config.py
│   ├── device.py
│   ├── diff.py
│   ├── dns.py
│   ├── doctor.py
│   ├── host.py
│   ├── interfaces.py
│   ├── ping.py
│   ├── ports.py
│   ├── report.py
│   ├── route.py
│   ├── scan.py
│   └── snapshot.py
├── config/
├── devices/
├── diagnostics/
├── network/
├── reports/
├── scanner/
│   ├── arp.py
│   ├── discovery.py
│   ├── icmp.py
│   └── tcp.py
├── snapshots/
└── utils/
```

---

# Discovery Architecture

The LAN scanner roughly follows this flow:

```text
                 ┌──────────────┐
                 │ CIDR network │
                 └──────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │ ICMP discovery│
                └───────┬───────┘
                        │
                ┌───────┴────────┐
                │                │
                ▼                ▼
           Reachable         Unreachable
                │
                ▼
        ┌───────────────┐
        │ MAC discovery │
        └───────┬───────┘
                │
        ┌───────┴───────────┐
        │                   │
        ▼                   ▼
   System ARP          Scapy fallback
        │
        ▼
   ┌──────────────┐
   │ Vendor lookup│
   └──────┬───────┘
          │
          ▼
   ┌──────────────────┐
   │ Hostname lookup  │
   └────────┬─────────┘
            │
     ┌──────┼───────────────┐
     │      │               │
     ▼      ▼               ▼
    SMB    DNS          /etc/hosts
                         + Bonjour
            │
            ▼
      ┌──────────────┐
      │ TCP scanning │
      └──────┬───────┘
             │
             ▼
        Final result
```

Each stage is best-effort.

Failure of one discovery method does not invalidate information obtained through another method.

---

# macOS Support

macOS receives additional integration through native utilities:

```text
ping
arp
smbutil
dns-sd
```

For example, MAC addresses can often be obtained from:

```bash
arp -an
```

SMB hostnames can sometimes be obtained through:

```bash
smbutil status <IP>
```

Bonjour services can be inspected manually with:

```bash
dns-sd -B _smb._tcp local
```

Some macOS network information is intentionally unavailable through standard DNS.

NetAudit therefore does not assume that every local device must have a reverse-DNS hostname.

---

# Privileges

Some operations may require elevated privileges depending on the operating system.

In particular:

- Raw ARP packet transmission
- Scapy packet capture
- Access to `/dev/bpf*` on macOS

If raw packet access is unavailable, NetAudit attempts to use safer system-level alternatives where possible.

A reachable host can still be reported as:

```text
UP
```

even if Scapy cannot access:

```text
/dev/bpf0
```

MAC discovery is optional metadata and must not turn a reachable host into `DOWN`.

---

# Security

NetAudit follows a safe-by-default approach.

The project is intended for authorized network auditing and diagnostics.

NetAudit:

- Does not exploit discovered services
- Does not attempt credential attacks
- Does not modify network devices
- Uses read-only device commands
- Does not intentionally fabricate discovery data
- Reports unavailable information explicitly
- Limits CIDR scanning
- Uses command timeouts to avoid indefinite blocking
- Treats MAC and hostname discovery as best-effort

> Only scan networks and systems that you own or have explicit authorization to audit.

---

---

# Support NetForge

<p align="center">
  <strong>Like NetAudit?</strong><br>
  Support the development of NetForge and future open-source network tools.
</p>

<p align="center">
  Every contribution helps fund development, testing, maintenance and new features.
</p>

### Crypto Donations

<table align="center">
<tr>
<td align="center" width="50%">

### 💵 USDT

**TRC-20**

```text
TYtLvfgG9szPoRUcNpsz3paYzynFmLS5Go
```

</td>
<td align="center" width="50%">

### 💎 TON

**TON Network**

```text
UQDpx5wZ03QD5tCFT6fkhKGJ-LRFhAfn7hYohEUSNoJcv6JS
```

</td>
</tr>
</table>

<p align="center">
  <strong>⚠️ Verify the network before sending</strong><br>
  <sub>USDT donations must be sent through TRC-20.</sub><br>
  <sub>Using the wrong network may result in permanent loss of funds.</sub>
</p>

<p align="center">
  <em>Thank you for supporting independent open-source development.</em>
</p>


# Development

Clone the repository:

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run Ruff:

```bash
ruff check netaudit tests
```

Run tests:

```bash
pytest -q
```

Run Mypy:

```bash
mypy netaudit
```

Run coverage:

```bash
pytest --cov=netaudit
```

---

# Testing

The project includes automated tests covering:

- CLI behavior
- Configuration
- Device connectors
- Diagnostics
- DNS
- Health checks
- ICMP
- Interfaces
- Reports
- Routing
- Services
- Snapshots
- TCP scanning
- Input validation

Before pushing changes:

```bash
ruff check netaudit tests
pytest -q
```

---

# CI/CD

GitHub Actions is used for automated project checks.

Repository:

https://github.com/netforge201/netaudit

---

# Roadmap

Planned improvements include:

- [ ] Better OUI/vendor database integration
- [ ] Extended Bonjour device discovery
- [ ] LLDP discovery
- [ ] CDP discovery
- [ ] SNMP support
- [ ] VLAN discovery
- [ ] Network topology mapping
- [ ] Device fingerprinting
- [ ] Improved service identification
- [ ] Historical network inventory
- [ ] SQLite storage
- [ ] Scheduled audits
- [ ] Prometheus metrics
- [ ] Webhook notifications
- [ ] Telegram notifications
- [ ] Slack notifications
- [ ] Plugin system
- [ ] Additional network vendors
- [ ] IPv6 discovery improvements

Roadmap items are not considered implemented until they are present in the actual codebase.

---

# Contributing

Contributions are welcome.

Before opening a pull request:

1. Run the test suite.
2. Run Ruff.
3. Run Mypy when applicable.
4. Add tests for new functionality.
5. Do not commit credentials.
6. Do not commit private network information.
7. Keep network-device functionality read-only.
8. Keep platform-specific behavior isolated where possible.
9. Do not introduce fake or guessed network results.

Example:

```bash
ruff check netaudit tests
pytest -q
```

---

# License

NetAudit is released under the MIT License.

See:

```text
LICENSE
```

for the full license text.

---

# Support

If NetAudit is useful to you, consider starring the repository and contributing improvements.

Repository:

https://github.com/netforge201/netaudit

Issues:

https://github.com/netforge201/netaudit/issues


---

# 🇷🇺 Русская версия

## Что такое NetAudit?

**NetAudit** — консольный инструмент для аудита, диагностики и анализа компьютерных сетей.

Он предназначен для сетевых инженеров, системных администраторов, специалистов по инфраструктуре, IT-support и студентов, изучающих сети и кибербезопасность.

NetAudit позволяет обнаруживать хосты, проверять их доступность, измерять задержку, получать MAC-адреса и информацию о производителе, определять hostname, сканировать TCP-порты, выполнять DNS-запросы, трассировать маршруты, анализировать локальные интерфейсы и работать с поддерживаемыми сетевыми устройствами.

Главный принцип проекта:

> NetAudit показывает только реально полученные данные и не подменяет отсутствующую информацию догадками.

## Возможности

### Обнаружение сети

- Сканирование CIDR-сетей.
- Параллельное обнаружение хостов.
- ICMP-проверка доступности.
- Измерение latency.
- Получение MAC-адресов.
- Использование системной ARP-таблицы.
- Поддержка macOS `arp`.
- Поддержка Linux neighbor table.
- Scapy как дополнительный механизм ARP.
- Нормализация MAC-адресов.
- Определение производителя по OUI.
- Определение производителя через `manuf`.
- Reverse DNS.
- `/etc/hosts`.
- SMB / NetBIOS на macOS.
- Bonjour / mDNS на macOS.
- TCP service discovery.
- Дополнительное сканирование портов.

### Диагностика

- Ping.
- Packet loss.
- Latency.
- TTL.
- DNS.
- Reverse DNS.
- Traceroute.
- Анализ интерфейсов.
- TCP scanning.
- HTTP/HTTPS checks.
- Health diagnostics.

### Сетевые устройства

Поддерживается read-only работа с:

```text
Cisco IOS / IOS-XE
Cisco NX-OS
Cisco IOS-XR
Juniper Junos
Arista EOS
Generic devices
```

Для подключения используется SSH/Netmiko.

## Установка

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
./install.sh
```

Или:

```bash
pip install .
```

Для разработки:

```bash
pip install -e ".[dev]"
```

## Быстрый старт

Сканирование сети:

```bash
netaudit scan 10.0.0.0/24
```

Сканирование с TCP-портами:

```bash
netaudit scan 10.0.0.0/24 --ports 22,80,443,445
```

JSON:

```bash
netaudit scan 10.0.0.0/24 --json
```

Информация о хосте:

```bash
netaudit host 10.0.0.1
```

Проверка портов:

```bash
netaudit ports 10.0.0.1 --range 1-1024
```

Ping:

```bash
netaudit ping 8.8.8.8
```

DNS:

```bash
netaudit dns example.com
```

Reverse DNS:

```bash
netaudit dns 8.8.8.8 --reverse
```

Traceroute:

```bash
netaudit route 8.8.8.8
```

Интерфейсы:

```bash
netaudit interfaces
```

Диагностика:

```bash
netaudit doctor 10.0.0.1
```

Информация о Cisco:

```bash
netaudit device info 10.0.0.1 --device-type cisco_ios
```

## MAC и Vendor

На macOS NetAudit в первую очередь использует системную ARP-таблицу:

```bash
arp -an
```

MAC-адреса macOS могут отображаться с однозначными hex-октетами. NetAudit нормализует их до стандартного шестнадцатеричного формата.

Например, синтетический пример:

```text
10.0.0.1 -> 00:11:22:33:44:55
```

Vendor определяется через базу `manuf` и встроенный OUI fallback.

Если производитель неизвестен, NetAudit показывает:

```text
VENDOR: —
```

Это означает только то, что соответствие не было найдено.

## Hostname

NetAudit использует несколько источников:

1. Reverse DNS.
2. `/etc/hosts`.
3. SMB / NetBIOS.
4. Bonjour / mDNS на macOS.

Hostname не всегда доступен. Это нормально для локальных сетей: устройство может отвечать на ICMP и иметь MAC-адрес, но не иметь PTR-записи или доступного имени.

## macOS

Для macOS используются системные инструменты:

```text
arp
smbutil
dns-sd
```

Некоторые Bonjour-запросы могут ждать ответ от сети. Поэтому NetAudit использует таймауты и не должен блокировать весь скан из-за одного устройства.

## Конфигурация

Основной конфигурационный файл:

```text
~/.netaudit/config.yaml
```

Пример:

```yaml
defaults:
  timeout: 2
  workers: 50

scanner:
  default_ports:
    - 22
    - 80
    - 443
    - 445

reports:
  directory: ./reports

snapshots:
  directory: ./snapshots
```

Также можно использовать переменные окружения с префиксом:

```text
NETAUDIT_*
```

## Безопасность

NetAudit предназначен для авторизованного аудита.

Инструмент:

- не пытается эксплуатировать найденные сервисы;
- не изменяет конфигурацию сетевых устройств;
- использует read-only команды;
- не должен сохранять credentials в отчётах;
- ограничивает размер CIDR-сканирования;
- сообщает об отсутствующих зависимостях и привилегиях;
- не выдумывает MAC, hostname или vendor.

> Используйте NetAudit только в сетях и системах, на аудит которых у вас есть разрешение.

## Разработка

```bash
ruff check netaudit tests
pytest -q
```

Type checking:

```bash
mypy netaudit
```

Coverage:

```bash
pytest --cov=netaudit
```

## Поддержать NetForge

Если NetAudit оказался полезен, можно поддержать разработку проекта криптодонатом.

### USDT — TRC-20

```text
TYtLvfgG9szPoRUcNpsz3paYzynFmLS5Go
```

### TON

```text
UQDpx5wZ03QD5tCFT6fkhKGJ-LRFhAfn7hYohEUSNoJcv6JS
```

Перед отправкой обязательно проверьте сеть. Для USDT используется именно **TRC-20**.

Спасибо за поддержку независимой open-source разработки.
