# StudyLock AI — Comprehensive Engineering Wiki

Welcome to the **StudyLock AI** Engineering & Architecture Wiki. This documentation repository provides in-depth specifications, architectural diagrams, operating-system integration strategies, data models, state machines, and operational guidelines conforming to the complete product specification.

---

## 🧭 System Overview & Core Principles

StudyLock AI is a student productivity platform designed to reduce digital distraction while making study planning measurable, transparent, and motivating. It pairs a local focus engine with platform-specific restriction adapters, task/calendar scheduling, progress analytics, and a cryptographic reward ledger.

### Diagram 1: Overall System Vision & Architectural Pillars

```mermaid
flowchart TD
    subgraph Pillars["StudyLock AI Core Pillars"]
        direction TB
        P1["🛡️ Honest Enforcement<br/>Show verified restrictions; never claim blocked unless confirmed by OS"]
        P2["⚡ Local-First Reliability<br/>Timers & schedules survive ordinary suspension, reboot & offline loss"]
        P3["🕊️ User Agency<br/>Always discoverable emergency exit with neutral exit logging"]
        P4["📈 Learning over Screen Time<br/>Reward goals & habits rather than raw open app duration"]
        P5["🔒 Privacy by Default<br/>Zero browsing history surveillance; minimal data collection"]
    end

    subgraph CoreEngine["Unified Core Focus Engine"]
        FSM["Focus Session State Machine<br/>(Monotonic Timestamps)"]
        Planner["Smart Planning Heuristics<br/>(0.35U + 0.30P + 0.20I + 0.15R)"]
        Ledger["Cryptographic Reward Ledger<br/>(Immutable Event Keys)"]
        Sync["Offline Outbox Sync<br/>(Delta Cursor & Tombstones)"]
    end

    Pillars --> CoreEngine
```

---

## 📱 Multi-Platform Adapter Matrix

StudyLock AI recognizes that no single API can control every device. It implements platform-specific adapters reporting exact enforcement states (`ACTIVE`, `PARTIAL`, `PERMISSION_REQUIRED`, `FAILED`).

### Diagram 2: Multi-Platform Capability Matrix & Adapter Topology

```mermaid
graph TD
    UserReq["User Study Plan & Desired Restrictions"] --> Router["Common Domain Policy Router"]

    Router --> |Main Frame URLs| Ext["Chrome / Edge MV3 Extension<br/>(DeclarativeNetRequest Redirector)"]
    Router --> |Desktop Processes| Win["Windows / macOS Daemon<br/>(Process Scanner & Helper)"]
    Router --> |Android Apps| And["Android Companion App<br/>(UsageStats + Accessibility + Room)"]
    Router --> |iOS Shields| IOS["iOS Companion App<br/>(ManagedSettings + FamilyControls)"]
    Router --> |Management| Web["Next.js Web Dashboard<br/>(Full 10 Screen Inventory)"]

    Ext --> ExtStatus["Status: ACTIVE (Domain Filtering)"]
    Win --> WinStatus["Status: ACTIVE (Process Restriction)"]
    And --> AndStatus["Status: ACTIVE (Usage Access)"]
    IOS --> IOSStatus["Status: PARTIAL (FamilyControls Entitlement)"]
    Web --> WebStatus["Status: ACTIVE (Planner & Ledger)"]
```

---

## 📚 Complete Wiki Documentation Index (30 Diagrams)

| Section | Topic | Diagrams Covered |
|---|---|---|
| **[01. System Architecture](01-System-Architecture)** | Layer boundaries, pipeline, and domain modules | **Diagrams 3, 4, 5** |
| **[02. Focus Session Engine](02-Focus-Session-Engine)** | State machine, monotonic math, and emergency exits | **Diagrams 6, 7, 8** |
| **[03. Platform Enforcement Adapters](03-Platform-Enforcement-Adapters)** | Browser extension, Android, Windows, and iOS adapters | **Diagrams 9, 10, 11, 12, 13** |
| **[04. Rule Engine & Precedence](04-Rule-Engine-and-Precedence)** | Rule precedence hierarchy, YouTube/Instagram matching | **Diagrams 14, 15** |
| **[05. Calendar Scheduling & Planner](05-Calendar-Scheduling-and-Planner)** | Recurrence, IANA timezones, and conflict detection | **Diagrams 16, 17, 18** |
| **[06. Tasks & Study Planning](06-Tasks-and-Study-Planning)** | Lifecycle states and task-linked focus sessions | **Diagrams 19, 20** |
| **[07. Cryptographic Reward Ledger](07-Cryptographic-Reward-Ledger)** | Idempotent XP issuance, streaks, and progression | **Diagrams 21, 22, 23** |
| **[08. Offline Sync Engine](08-Offline-Sync-Engine)** | Durable outbox, conflict merges, and tombstones | **Diagrams 24, 25, 26** |
| **[09. Security, Privacy & Threat Model](09-Security-Privacy-and-Threat-Model)** | IDOR checks, data sovereignty, and GDPR purge | **Diagrams 27, 28, 29** |
| **[10. Observability, Deployment & CI/CD](10-Observability-Deployment-and-Operations)** | Observability metrics, heartbeats, and Vercel/Docker CI | **Diagram 30** |
