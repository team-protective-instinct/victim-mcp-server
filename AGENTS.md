# AI Agent Instructions for capstone-victim

> **Workspace context**: This is part of a multi-project workspace. See root [AGENTS.md](../AGENTS.md) for overall architecture, data flow, and startup order.

## Overview

Vulnerable targets (DVWA, Metasploitable2) + automated attack scripts. Generates security logs that flow through ELK to the backend AI agent.

## Commands

- **Package manager**: `uv`. Run the unified script via `uv run attack.py -s <N>` for DVWA or `uv run attack.py -m <N>` / `uv run attack.py` for Metasploitable2.
- **Infrastructure**: `docker compose up -d` (WAF, Metasploitable2, Filebeat)

## Attack scripts

### attack.py — DVWA scenarios (1-5, 11-15)
- Scenarios 1-5: Basic DVWA attacks (Brute Force, Command Injection, SQLi, File Upload, XSS)
- Scenarios 11-15: Integrated (penetration + post-exploitation)
- Run: `uv run attack.py -s <1-5|11-15>`

### attack.py — Metasploitable2 scenarios (1-13)
- Run: `uv run attack.py -m <1-13>` or `uv run attack.py`, then select interactively
- 10 direct exploit scenarios + batch options

## Infrastructure

Docker Compose services:
- **WAF**: ModSecurity/nginx on port 80 (proxies to DVWA)
- **Metasploitable2**: Ports 21, 22, 139, 445, 3632, 6200, 6667, 8180
- **Filebeat**: Ships logs to Logstash via `elk-stack` network

## Log collection

Filebeat ships:
- WAF audit logs: `/var/log/modsecurity/audit.log`
- Metasploitable2 logs: syslog, auth.log, daemon.log

Target: `logstash:5044` via `elk-stack` network

## Prerequisites

- `elk-stack` Docker network must exist: `docker network create elk-stack`
- DVWA auto-login: admin/password
