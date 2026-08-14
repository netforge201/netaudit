# NetAudit

<p align="center">
  <strong>Network Audit & Diagnostics Toolkit</strong><br>
  A practical, scriptable CLI for network engineers, system administrators and infrastructure professionals.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#commands">Commands</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#supported-devices">Devices</a> •
  <a href="#development">Development</a>
</p>

<p align="center">
  <a href="#русская-версия">🇷🇺 Русская версия</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Platform-macOS%20%7C%20Linux-111111?style=for-the-badge" alt="Platform">
  <img src="https://img.shields.io/badge/Interface-CLI-orange?style=for-the-badge" alt="CLI">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="MIT">
</p>

---

## Overview

**NetAudit** is a command-line toolkit for network auditing, diagnostics and infrastructure visibility.

It is designed for network engineers, system administrators, cybersecurity students and infrastructure professionals who want practical network checks directly from the terminal.

NetAudit can discover hosts, inspect local interfaces, test connectivity, scan TCP ports, query DNS, trace routes, connect to supported network devices, create device snapshots, compare state changes and generate structured reports.

### Core principles

- **Real results** — NetAudit reports actual observations rather than simulated data.
- **Safe by default** — network-device operations are read-only.
- **CLI first** — designed for terminals, scripts and automation.
- **Machine friendly** — structured output and useful exit codes.
- **Vendor aware** — supports common enterprise network platforms.
- **Transparent failures** — unavailable checks are reported instead of guessed.

> Use NetAudit only on systems and networks you own or are explicitly authorized to audit.

---

## Features

- Host discovery across CIDR ranges
- Concurrent ICMP discovery
- TCP connect port scanning
- Ping and latency diagnostics
- DNS lookups and reverse DNS
- Route tracing
- Local network interface inspection
- Network device access over SSH
- Cisco, Juniper and Arista support
- Device health diagnostics
- Interface, route, ARP, NTP, BGP and OSPF checks where supported
- Device snapshots
- Snapshot comparison
- JSON reports
- CSV reports
- Markdown reports
- Self-contained HTML reports
- Configuration through YAML and environment variables
- Shell and CI/CD friendly output
- Automated tests and GitHub Actions

---

## CLI Overview

```text
Usage: netaudit COMMAND [OPTIONS]

Commands:
  scan          Discover live hosts on a network
  host          Inspect a single host
  ports         Scan TCP ports
  ping          Test reachability and latency
  dns           Perform DNS lookups
  route         Trace a network route
  interfaces    Inspect local network interfaces
  device        Query supported network devices
  snapshot      Create or list device snapshots
  diff          Compare device snapshots
  doctor        Run network health diagnostics
  report        Generate reports
  config        Manage configuration
```

---

# Installation

## Requirements

- Python 3.11+
- macOS or Linux
- Windows support is best-effort

## Quick install

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
./install.sh
```

The installer uses `pipx` when available. Otherwise, it creates a local virtual environment and installs NetAudit there.

## Manual installation

```bash
pip install .
```

For development:

```bash
pip install -e ".[dev]"
```

## Wrapper

The repository also includes a wrapper that can create and use the project's virtual environment automatically:

```bash
./netaudit.sh scan 192.168.1.0/24
```

---

# Quick Start

## Discover hosts

```bash
netaudit scan 192.168.1.0/24
```

Check selected ports while discovering:

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443
```

Export results:

```bash
netaudit scan 192.168.1.0/24 --json > scan.json
```

## Inspect a host

```bash
netaudit host 192.168.1.1
```

## Scan TCP ports

```bash
netaudit ports 192.168.1.1
```

Custom range:

```bash
netaudit ports 192.168.1.1 --range 1-1024
```

## Ping

```bash
netaudit ping 8.8.8.8
```

## DNS

```bash
netaudit dns example.com
```

Reverse DNS:

```bash
netaudit dns 8.8.8.8 --reverse
```

## Trace route

```bash
netaudit route 8.8.8.8
```

## Inspect local interfaces

```bash
netaudit interfaces
```

## Run diagnostics

```bash
netaudit doctor 192.168.1.1
```

## Query a Cisco device

```bash
netaudit device info 192.168.1.1 --device-type cisco_ios
```

---

# Commands

## `scan`

Discover live hosts in a CIDR range.

```bash
netaudit scan 192.168.1.0/24
netaudit scan 192.168.1.0/24 --ports 22,80,443
netaudit scan 10.0.0.0/24 --timeout 0.5 --workers 100 --json
```

Common options:

| Option | Description |
|---|---|
| `--timeout` | Per-host timeout |
| `--workers` | Number of concurrent workers |
| `--ports` | Additional TCP ports |
| `--json` | JSON output |
| `--csv` | CSV output |
| `--quiet` | Reduce progress output |

NetAudit limits CIDR scanning to 65,536 addresses to reduce the risk of accidental large-scale scans.

---

## `host`

Inspect a single host.

Depending on what is available, the result can include:

- Reachability
- Latency
- TTL / OS hint
- Reverse DNS
- MAC address
- Vendor
- Common service ports

MAC and vendor information is only shown when it can actually be obtained.

---

## `ports`

Perform a TCP connect scan.

```bash
netaudit ports 192.168.1.1
netaudit ports 192.168.1.1 --ports 22,80,443
netaudit ports 192.168.1.1 --range 1-1024
```

NetAudit does not attempt to exploit discovered services.

---

## `ping`

Measure reachability and latency using the operating system's native networking utilities.

```bash
netaudit ping 8.8.8.8
netaudit ping 8.8.8.8 --count 10
```

---

## `dns`

Perform DNS queries.

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

Trace the route to a destination.

```bash
netaudit route 8.8.8.8
```

NetAudit uses the platform's available route-tracing utility.

---

## `interfaces`

Inspect local interfaces:

```bash
netaudit interfaces
```

Depending on the platform, information can include:

- Interface name
- State
- MAC address
- IPv4 / IPv6 addresses
- MTU
- RX statistics
- TX statistics

---

## `device`

Connect to supported network devices over SSH.

Example:

```bash
netaudit device connect 192.168.1.1 --device-type cisco_ios
```

Get device information:

```bash
netaudit device info 192.168.1.1 --device-type cisco_ios
```

All device operations are designed to be read-only.

---

## `snapshot`

Capture device state:

```bash
netaudit snapshot 192.168.1.1 --device-type cisco_ios
```

List snapshots:

```bash
netaudit snapshot --list
```

List snapshots for a device:

```bash
netaudit snapshot --list 192.168.1.1
```

---

## `diff`

Compare device snapshots:

```bash
netaudit diff 192.168.1.1
```

This helps identify changes between recorded device states.

---

## `doctor`

Run a comprehensive health check:

```bash
netaudit doctor 192.168.1.1
```

For a network device:

```bash
netaudit doctor 192.168.1.1 --device --device-type cisco_ios
```

Depending on the target and platform, diagnostics can include:

- Reachability
- Latency
- Packet loss
- DNS
- SSH
- HTTP / HTTPS
- Open services
- Interface state
- Interface errors
- Uptime
- Default route
- ARP
- NTP
- BGP
- OSPF

Unsupported checks are reported as unavailable/skipped rather than replaced with estimated data.

---

## `report`

Generate reports from saved results.

HTML:

```bash
netaudit report scan.json --format html
```

Markdown:

```bash
netaudit report scan.json --format markdown --output report.md
```

Supported formats:

```text
JSON
CSV
Markdown
HTML
```

---

## `config`

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

---

# Configuration

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

reports:
  directory: ./reports

snapshots:
  directory: ./snapshots
```

Configuration values can also be overridden through `NETAUDIT_*` environment variables.

See `config.example.yaml` and `.env.example` for examples.

---

# Credentials

Network-device credentials should not be committed to Git.

Credential resolution can use:

1. CLI options
2. Environment variables
3. Interactive hidden password input

Example environment variables:

```bash
export NETAUDIT_USERNAME="admin"
export NETAUDIT_PASSWORD="your-password"
```

Avoid putting real credentials into:

- Git repositories
- README files
- screenshots
- issue reports
- shell history
- public configuration files

---

# Supported Devices

| Vendor | Device Type | Access |
|---|---|---|
| Cisco IOS / IOS-XE | `cisco_ios` | Read-only |
| Cisco NX-OS | `cisco_nxos` | Read-only |
| Cisco IOS-XR | `cisco_xr` | Read-only |
| Juniper Junos | `juniper_junos` | Read-only |
| Arista EOS | `arista_eos` | Read-only |
| Generic | `generic` | Read-only |

---

# Security

NetAudit follows a safe-by-default model.

- No device configuration changes
- No exploitation of discovered services
- No credential storage in reports
- CIDR scan limit
- Explicit privilege/dependency errors
- No fabricated results
- Unsupported checks are skipped/reported
- Read-only network-device commands

NetAudit is an auditing and diagnostics tool, not an exploitation framework.

> Only scan and audit systems for which you have authorization.

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
├── snapshots/
└── utils/
```

### Design principles

**Thin CLI layer**

Commands handle arguments and presentation while reusable logic stays in dedicated modules.

**stdout = results**

**stderr = logs**

This makes NetAudit suitable for:

```text
jq
grep
awk
shell pipelines
CI/CD
automation
```

**Never fake a result**

If a check cannot be performed, NetAudit reports why.

---

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

Run linting:

```bash
ruff check netaudit tests
```

Run type checking:

```bash
mypy netaudit
```

Run tests:

```bash
pytest
```

Run coverage:

```bash
pytest --cov=netaudit
```

---

# Testing

The test suite mocks external network and device operations where appropriate.

Covered areas include:

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
- Validation

The project also includes GitHub Actions workflows for automated checks.

---

# Contributing

Contributions are welcome.

Before opening a pull request:

1. Run the test suite.
2. Run linting.
3. Add tests for new functionality.
4. Do not commit credentials.
5. Do not commit private infrastructure information.
6. Keep new functionality consistent with the project's read-only and safe-by-default approach.

Please check the repository's issue and pull-request templates before contributing.

---

# Roadmap

Planned improvements include:

- [ ] SNMP support
- [ ] LLDP / CDP discovery
- [ ] VLAN discovery
- [ ] Extended BGP / OSPF monitoring
- [ ] Interface utilization graphs
- [ ] Network topology mapping
- [ ] Scheduled audits
- [ ] Historical SQLite storage
- [ ] Prometheus metrics
- [ ] Webhook notifications
- [ ] Slack notifications
- [ ] Telegram notifications
- [ ] Plugin system
- [ ] Additional network vendors

Roadmap items are planned features and should not be considered implemented until they appear in the actual release.

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

---

# 🇷🇺 Русская версия

## Что такое NetAudit?

**NetAudit** — консольный инструмент для аудита, диагностики и анализа компьютерных сетей.

Он предназначен для:

- сетевых инженеров;
- системных администраторов;
- специалистов по инфраструктуре;
- студентов и начинающих специалистов по сетям и кибербезопасности.

NetAudit позволяет обнаруживать хосты, проверять доступность, измерять задержку, сканировать TCP-порты, выполнять DNS-запросы, трассировать маршруты, анализировать локальные интерфейсы, подключаться к сетевым устройствам, создавать snapshots и сравнивать изменения.

### Основные принципы

- **Реальные результаты** — никаких выдуманных данных.
- **Safe by default** — сетевые устройства работают в read-only режиме.
- **CLI first** — инструмент создан для терминала.
- **Automation friendly** — подходит для shell и CI/CD.
- **Прозрачные ошибки** — если проверка невозможна, причина сообщается явно.
- **Поддержка оборудования** — Cisco, Juniper, Arista и generic devices.

> Используйте NetAudit только в сетях и системах, на аудит которых у вас есть разрешение.

---

## Возможности

- Обнаружение хостов в CIDR
- Параллельный ICMP discovery
- TCP connect scanning
- Ping и диагностика latency
- DNS и reverse DNS
- Traceroute
- Анализ локальных интерфейсов
- SSH-доступ к сетевым устройствам
- Cisco / Juniper / Arista
- Health diagnostics
- Проверка интерфейсов, маршрутов, ARP, NTP, BGP и OSPF там, где это поддерживается
- Snapshots
- Сравнение snapshots
- JSON / CSV / Markdown / HTML reports
- YAML configuration
- Environment variables
- Automated tests
- GitHub Actions

---

# Установка

## Требования

- Python 3.11+
- macOS или Linux
- Windows поддерживается в режиме best-effort

## Быстрая установка

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
./install.sh
```

## Ручная установка

```bash
pip install .
```

Для разработки:

```bash
pip install -e ".[dev]"
```

## Wrapper

```bash
./netaudit.sh scan 192.168.1.0/24
```

---

# Быстрый старт

Поиск устройств:

```bash
netaudit scan 192.168.1.0/24
```

Поиск и проверка портов:

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443
```

JSON:

```bash
netaudit scan 192.168.1.0/24 --json > scan.json
```

Информация о хосте:

```bash
netaudit host 192.168.1.1
```

Порты:

```bash
netaudit ports 192.168.1.1 --range 1-1024
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
netaudit doctor 192.168.1.1
```

Cisco:

```bash
netaudit device info 192.168.1.1 --device-type cisco_ios
```

---

# Команды

## `scan`

Обнаружение активных хостов:

```bash
netaudit scan 192.168.1.0/24
```

Параметры:

| Параметр | Описание |
|---|---|
| `--timeout` | Таймаут |
| `--workers` | Количество workers |
| `--ports` | Дополнительные TCP-порты |
| `--json` | JSON |
| `--csv` | CSV |
| `--quiet` | Минимальный вывод |

---

## `host`

Подробная информация о хосте:

- доступность;
- latency;
- TTL / OS hint;
- reverse DNS;
- MAC;
- vendor;
- стандартные сервисные порты.

---

## `ports`

```bash
netaudit ports 192.168.1.1
netaudit ports 192.168.1.1 --ports 22,80,443
netaudit ports 192.168.1.1 --range 1-1024
```

Используется TCP connect scan.

NetAudit не пытается эксплуатировать найденные сервисы.

---

## `ping`

```bash
netaudit ping 8.8.8.8
netaudit ping 8.8.8.8 --count 10
```

---

## `dns`

```bash
netaudit dns example.com
netaudit dns 8.8.8.8 --reverse
```

Поддерживаются:

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

```bash
netaudit route 8.8.8.8
```

---

## `interfaces`

```bash
netaudit interfaces
```

Может показывать:

- интерфейсы;
- состояние;
- MAC;
- IPv4 / IPv6;
- MTU;
- RX;
- TX.

---

## `device`

Подключение:

```bash
netaudit device connect 192.168.1.1 --device-type cisco_ios
```

Информация:

```bash
netaudit device info 192.168.1.1 --device-type cisco_ios
```

Поддерживаются:

```text
cisco_ios
cisco_nxos
cisco_xr
juniper_junos
arista_eos
generic
```

Все операции с устройствами являются read-only.

---

## `snapshot`

Создать snapshot:

```bash
netaudit snapshot 192.168.1.1 --device-type cisco_ios
```

Список:

```bash
netaudit snapshot --list
```

---

## `diff`

Сравнение snapshots:

```bash
netaudit diff 192.168.1.1
```

---

## `doctor`

```bash
netaudit doctor 192.168.1.1
```

Для сетевого устройства:

```bash
netaudit doctor 192.168.1.1 --device --device-type cisco_ios
```

В зависимости от устройства проверяются:

- доступность;
- latency;
- packet loss;
- DNS;
- SSH;
- HTTP / HTTPS;
- сервисы;
- интерфейсы;
- ошибки интерфейсов;
- uptime;
- default route;
- ARP;
- NTP;
- BGP;
- OSPF.

Неподдерживаемые проверки не подменяются выдуманными результатами.

---

## `report`

HTML:

```bash
netaudit report scan.json --format html
```

Markdown:

```bash
netaudit report scan.json --format markdown --output report.md
```

Форматы:

```text
JSON
CSV
Markdown
HTML
```

---

## `config`

```bash
netaudit config init
netaudit config show
```

Файл:

```text
~/.netaudit/config.yaml
```

---

# Конфигурация

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

reports:
  directory: ./reports

snapshots:
  directory: ./snapshots
```

Также доступны переменные окружения с префиксом `NETAUDIT_*`.

---

# Credentials

Не храните реальные credentials в Git.

NetAudit может использовать:

1. CLI options
2. Environment variables
3. Interactive hidden prompt

Пример:

```bash
export NETAUDIT_USERNAME="admin"
export NETAUDIT_PASSWORD="your-password"
```

Не добавляйте реальные пароли в:

- Git;
- README;
- screenshots;
- issues;
- публичные config-файлы.

---

# Поддерживаемые устройства

| Производитель | Тип | Режим |
|---|---|---|
| Cisco IOS / IOS-XE | `cisco_ios` | Read-only |
| Cisco NX-OS | `cisco_nxos` | Read-only |
| Cisco IOS-XR | `cisco_xr` | Read-only |
| Juniper Junos | `juniper_junos` | Read-only |
| Arista EOS | `arista_eos` | Read-only |
| Generic | `generic` | Read-only |

---

# Безопасность

NetAudit работает по принципу safe-by-default.

- Не изменяет конфигурацию устройств.
- Не эксплуатирует обнаруженные сервисы.
- Не записывает credentials в отчёты.
- Ограничивает CIDR scan.
- Сообщает об отсутствии привилегий.
- Сообщает об отсутствующих зависимостях.
- Не подменяет неизвестные данные.
- Использует read-only команды для сетевых устройств.

---

# Архитектура

```text
netaudit/
├── cli.py
├── commands/
├── scanner/
├── network/
├── devices/
├── diagnostics/
├── snapshots/
├── reports/
├── config/
└── utils/
```

Основные принципы:

```text
stdout → результаты
stderr → логи
```

NetAudit удобно использовать с:

```text
jq
grep
awk
shell pipelines
CI/CD
automation
```

---

# Разработка

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
pip install -e ".[dev]"
```

Lint:

```bash
ruff check netaudit tests
```

Type checking:

```bash
mypy netaudit
```

Tests:

```bash
pytest
```

Coverage:

```bash
pytest --cov=netaudit
```

---

# Тестирование

Проект содержит тесты для:

- CLI;
- configuration;
- device connector;
- diagnostics;
- DNS;
- health;
- ICMP;
- interfaces;
- reports;
- routing;
- services;
- snapshots;
- TCP scanner;
- validators.

Внешние сетевые операции и подключения к устройствам там, где это необходимо, заменяются mock-объектами.

---

# Contributing

Pull Requests и Issues приветствуются.

Перед PR:

1. Запустите `pytest`.
2. Запустите `ruff check netaudit tests`.
3. Добавьте тесты для нового функционала.
4. Не добавляйте credentials.
5. Не добавляйте приватные IP/hostname production-инфраструктуры.
6. Соблюдайте safe-by-default подход проекта.

---

# Roadmap

Планируется:

- [ ] SNMP
- [ ] LLDP / CDP discovery
- [ ] VLAN discovery
- [ ] Расширенный BGP / OSPF monitoring
- [ ] Interface utilization graphs
- [ ] Network topology mapping
- [ ] Scheduled audits
- [ ] SQLite history
- [ ] Prometheus metrics
- [ ] Webhook notifications
- [ ] Slack notifications
- [ ] Telegram notifications
- [ ] Plugin system
- [ ] Additional network vendors

Roadmap содержит планируемые функции и не означает, что они уже реализованы.

---

# Support NetForge

<p align="center">
  <strong>Like NetAudit?</strong><br>
  Support the development of NetForge and future open-source network tools.
</p>

<p align="center">
  Your support helps with development, testing, maintenance and new features.
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
  <sub>Sending through the wrong network may result in permanent loss of funds.</sub>
</p>

<p align="center">
  <em>Thank you for supporting independent open-source development.</em>
</p>

---

# License

NetAudit is released under the MIT License.

See `LICENSE`.

---

# 🇷🇺 Русская версия

## Что такое NetAudit?

**NetAudit** — консольный toolkit для аудита, диагностики и анализа компьютерных сетей.

Он предназначен для сетевых инженеров, системных администраторов, специалистов по инфраструктуре и студентов, изучающих сети и кибербезопасность.

NetAudit позволяет обнаруживать хосты, проверять доступность, измерять задержку, сканировать TCP-порты, выполнять DNS-запросы, трассировать маршруты, анализировать интерфейсы, подключаться к сетевым устройствам, создавать snapshots и сравнивать изменения.

### Основные принципы

- Реальные результаты.
- Никаких фейковых данных.
- Safe by default.
- Read-only операции с сетевыми устройствами.
- CLI-first подход.
- Поддержка автоматизации.
- Прозрачные ошибки.

> Используйте NetAudit только в сетях и системах, которые принадлежат вам или на аудит которых у вас есть разрешение.

---

## Возможности

- Обнаружение хостов
- ICMP discovery
- TCP port scanning
- Ping и latency
- DNS и reverse DNS
- Traceroute
- Анализ интерфейсов
- SSH к сетевым устройствам
- Cisco / Juniper / Arista
- Health diagnostics
- BGP / OSPF проверки там, где поддерживаются
- Snapshots
- Diff
- JSON / CSV / Markdown / HTML reports
- YAML configuration
- Environment variables
- Automated tests
- GitHub Actions

---

# Установка

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
./install.sh
```

Ручная установка:

```bash
pip install .
```

Для разработки:

```bash
pip install -e ".[dev]"
```

Wrapper:

```bash
./netaudit.sh scan 192.168.1.0/24
```

---

# Быстрый старт

```bash
netaudit scan 192.168.1.0/24
```

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443
```

```bash
netaudit host 192.168.1.1
```

```bash
netaudit ports 192.168.1.1 --range 1-1024
```

```bash
netaudit ping 8.8.8.8
```

```bash
netaudit dns example.com
```

```bash
netaudit route 8.8.8.8
```

```bash
netaudit interfaces
```

```bash
netaudit doctor 192.168.1.1
```

```bash
netaudit device info 192.168.1.1 --device-type cisco_ios
```

---

# Команды

## `scan`

```bash
netaudit scan 192.168.1.0/24
```

Дополнительные порты:

```bash
netaudit scan 192.168.1.0/24 --ports 22,80,443
```

JSON:

```bash
netaudit scan 192.168.1.0/24 --json
```

---

## `host`

Показывает доступность, latency, TTL / OS hint, reverse DNS и доступные сведения о MAC/vendor.

---

## `ports`

```bash
netaudit ports 192.168.1.1
netaudit ports 192.168.1.1 --ports 22,80,443
netaudit ports 192.168.1.1 --range 1-1024
```

---

## `ping`

```bash
netaudit ping 8.8.8.8
```

---

## `dns`

```bash
netaudit dns example.com
```

Reverse DNS:

```bash
netaudit dns 8.8.8.8 --reverse
```

---

## `route`

```bash
netaudit route 8.8.8.8
```

---

## `interfaces`

```bash
netaudit interfaces
```

---

## `device`

```bash
netaudit device connect 192.168.1.1 --device-type cisco_ios
```

```bash
netaudit device info 192.168.1.1 --device-type cisco_ios
```

Поддерживаются:

```text
cisco_ios
cisco_nxos
cisco_xr
juniper_junos
arista_eos
generic
```

Все операции read-only.

---

## `snapshot`

```bash
netaudit snapshot 192.168.1.1 --device-type cisco_ios
```

```bash
netaudit snapshot --list
```

---

## `diff`

```bash
netaudit diff 192.168.1.1
```

---

## `doctor`

```bash
netaudit doctor 192.168.1.1
```

Для сетевого устройства:

```bash
netaudit doctor 192.168.1.1 --device --device-type cisco_ios
```

---

## `report`

```bash
netaudit report scan.json --format html
```

```bash
netaudit report scan.json --format markdown --output report.md
```

---

## `config`

```bash
netaudit config init
netaudit config show
```

Конфигурация:

```text
~/.netaudit/config.yaml
```

---

# Конфигурация

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

reports:
  directory: ./reports

snapshots:
  directory: ./snapshots
```

---

# Безопасность

NetAudit:

- не изменяет конфигурацию устройств;
- не эксплуатирует найденные сервисы;
- не сохраняет credentials в отчётах;
- ограничивает размер CIDR scan;
- сообщает о недостающих правах;
- сообщает о недоступных функциях;
- не выдумывает результаты;
- использует read-only команды.

---

# Разработка

```bash
git clone https://github.com/netforge201/netaudit.git
cd netaudit
pip install -e ".[dev]"
```

```bash
ruff check netaudit tests
```

```bash
mypy netaudit
```

```bash
pytest
```

```bash
pytest --cov=netaudit
```

---

# Roadmap

- [ ] SNMP
- [ ] LLDP / CDP
- [ ] VLAN discovery
- [ ] BGP / OSPF monitoring
- [ ] Interface graphs
- [ ] Network topology
- [ ] Scheduled audits
- [ ] SQLite history
- [ ] Prometheus metrics
- [ ] Webhooks
- [ ] Slack
- [ ] Telegram
- [ ] Plugin system
- [ ] Additional vendors

---

# Поддержать NetForge

<p align="center">
  <strong>Нравится NetAudit?</strong><br>
  Поддержите разработку NetForge и будущих open-source сетевых инструментов.
</p>

<p align="center">
  Ваша поддержка помогает развивать проект, тестировать новые функции и поддерживать существующие инструменты.
</p>

### Криптодонаты

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
  <strong>⚠️ Обязательно проверьте сеть перед отправкой</strong><br>
  <sub>USDT необходимо отправлять через сеть TRC-20.</sub><br>
  <sub>Использование неправильной сети может привести к безвозвратной потере средств.</sub>
</p>

<p align="center">
  <em>Спасибо за поддержку независимой open-source разработки.</em>
</p>

---

# License

NetAudit распространяется под MIT License.

См. `LICENSE`.

---

<p align="center">
  <strong>NetForge</strong><br>
  Building practical tools for modern networks.
</p>
