# AI Agent Instructions for capstone-victim

> **Workspace context**: This is part of a multi-project workspace. See root [AGENTS.md](../AGENTS.md) for overall architecture, data flow, and startup order.

## Overview

Vulnerable targets (DVWA) + automated attack scripts. Generates security logs that flow through ELK to the backend AI agent.

## Commands

- **Package manager**: `uv`. Run the unified script via `uv run attack.py -s <N>` for DVWA.
- **Infrastructure**: `docker compose up -d` (DVWA, Filebeat)

## Attack scripts

### attack.py — DVWA scenarios (1-10)
- Scenarios 1-5: Basic DVWA attacks (Brute Force, Command Injection, SQLi, File Upload, XSS)
- Scenarios 6-10: Integrated (penetration + post-exploitation)
- Run: `uv run attack.py -s <1-10>`

## Infrastructure

Docker Compose services:
- **DVWA**: Port 8080
- **Filebeat**: Ships logs to Logstash via `elk-stack` network

## Log collection

Filebeat ships:
- DVWA Apache logs: `/var/log/dvwa/access.log`, `/var/log/dvwa/error.log`

Target: `logstash:5044` via `elk-stack` network

## Prerequisites

- `elk-stack` Docker network must exist: `docker network create elk-stack`
- DVWA auto-login: admin/password
