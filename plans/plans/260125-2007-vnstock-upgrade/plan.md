---
title: "vnstock 3.x Migration"
description: "Upgrade trading bot from vnstock 1.x to 3.x API with expanded exchange support"
status: validated
priority: P1
effort: 4h
branch: main
tags: [vnstock, migration, python, trading-bot]
created: 2026-01-25
---

# vnstock 3.x Migration Plan

## Overview

Migrate trading bot from deprecated `stock_historical_data()` API to vnstock 3.x OOP classes (`Quote`, `Listing`). Add support for scanning HOSE/HNX exchanges dynamically. (UPCOM skipped per validation)

## Context Links

- [vnstock 3.x API Research](./research/researcher-01-vnstock-api.md)
- [Technical Indicators Research](./research/researcher-02-technical-indicators.md)
- [Brainstorm Report](../reports/brainstorm-260125-2007-vnstock-integration-upgrade.md)

## Phase Summary

| Phase | Description | Priority | Status | Effort |
|-------|-------------|----------|--------|--------|
| [Phase 1](./phase-01-fix-critical-issues.md) | Fix Critical Issues | P1 | pending | 1h |
| [Phase 2](./phase-02-expand-data-sources.md) | Expand Data Sources | P1 | pending | 1h |
| [Phase 3](./phase-03-enhance-analysis.md) | Enhance Analysis | P2 | pending | 1h |
| [Phase 4](./phase-04-production-ready.md) | Production Ready | P2 | pending | 1h |

## Critical Path

```
Phase 1 (Fix Critical) --> Phase 2 (Expand Data) --> Phase 3 (Analysis) --> Phase 4 (Production)
     |                          |
     +-- vnstock 3.x API        +-- Listing class for dynamic symbols
     +-- YAML syntax fix        +-- VnstockClient wrapper
     +-- argparse setup
```

## Files to Modify

| File | Phase | Action |
|------|-------|--------|
| `src/__init__.py` | 1 | CREATE |
| `src/data_fetcher.py` | 1 | MODIFY (migrate to Quote) |
| `src/config.py` | 1 | MODIFY (add DATA_SOURCE, API_KEY) |
| `src/bot.py` | 1 | MODIFY (add argparse) |
| `.github/workflows/*.yml` | 1 | MODIFY (fix syntax) |
| `src/data/listing.py` | 2 | CREATE |
| `src/data/fetcher.py` | 2 | CREATE (VnstockClient) |
| `src/indicators.py` | 3 | MODIFY (add Stochastic, ADX, OBV, MFI) |
| `src/notifier.py` | 3 | MODIFY (add summary report) |
| `src/utils/rate_limiter.py` | 4 | CREATE |
| `requirements.txt` | 4 | MODIFY (pin versions) |

## Key Dependencies

- vnstock >= 3.4.0
- pandas >= 2.0.0
- numpy >= 1.24.0

## Success Criteria

- [ ] Bot runs without deprecation warnings
- [ ] Scans HOSE/HNX via `--exchange` argument
- [ ] GitHub Actions workflows pass
- [ ] Telegram notifications work
- [ ] Rate limiting prevents API blocks

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| API rate limit exceeded | Add 0.5s delay between requests |
| vnstock API changes | Pin version in requirements.txt |
| VCI source fails | Fallback to KBS automatically |

---

## Validation Summary

**Validated:** 2026-01-25
**Questions asked:** 6

### Confirmed Decisions

| Decision | User Choice |
|----------|-------------|
| Data Source | VCI primary + KBS fallback |
| UPCOM handling | Skip UPCOM, only HOSE + HNX |
| New Indicators | All 4: Stochastic, ADX, OBV, MFI |
| MIN_SCORE threshold | Keep at 4 |
| Backward compatibility | Keep `data_fetcher.py` as wrapper |
| Error notification | Log only, no Telegram error alerts |

### Action Items (Plan Changes Applied)

- [x] Update config.py: Add fallback logic VCI → KBS
- [x] Remove `upcom_scan.yml` workflow (delete in phase-01)
- [x] Update plan.md: Remove UPCOM references
- [x] Update phase-01: Remove UPCOM workflow fix
- [x] Confirm all 4 new indicators in phase-03
