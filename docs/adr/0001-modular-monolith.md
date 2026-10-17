# ADR 0001: Modular Monolith

## Status

Accepted

## Context

StockTill needs Clean Architecture boundaries without the operational complexity of microservices.

## Decision

Use a modular monolith with clear bounded contexts. Each context has its own domain, application, infrastructure, and interfaces layers. Contexts communicate through ports and adapters, not direct model imports.

## Consequences

- Single deployable unit
- Clear boundaries enforced by import-linter
- Easy to extract a service later if needed
- No distributed transaction overhead
