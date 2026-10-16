# 05. Calendar Scheduling & AI Planner

StudyLock AI provides automated study schedule generation, overlap conflict detection, and IANA timezone-aware recurrence.

---

## 🎯 Smart Planning Composite Scoring

Candidate study tasks are ranked using a multi-factor heuristic formula defined in Section 8.4:

$$\text{Score} = 0.35 \times \text{Urgency} + 0.30 \times \text{Priority} + 0.20 \times \text{Importance} + 0.15 \times \text{Readiness}$$

### Diagram 16: Smart Planner Composite Scoring Pipeline

```mermaid
flowchart LR
    Task["Candidate Task"] --> Extractor["Extract Normalized Factors (0..100)"]

    Extractor --> U["Deadline Urgency (0.35)<br/>Overdue / <2h: 100<br/>24h: 80..100<br/>3d: 50..80"]
    Extractor --> P["User Priority (0.30)<br/>Critical: 100<br/>High: 75<br/>Med: 50 | Low: 25"]
    Extractor --> I["Goal Importance (0.20)<br/>Course weight / user tag"]
    Extractor --> R["Readiness (0.15)<br/>Prerequisites completed"]

    U & P & I & R --> WeightedSum["Composite Score Calculation"]
    WeightedSum --> PinnedCheck{"Task User-Pinned?"}
    PinnedCheck --> |Yes| TopRank["Rank at Top of Schedule"]
    PinnedCheck --> |No| OrderedRank["Sort Descending by Score"]
```

---

## 📅 Calendar Overlap Detection & Conflict Engine

The engine identifies conflicting focus blocks and recommends intelligent, non-destructive resolution.

### Diagram 17: Calendar Overlap Detection & Conflict Resolution Flow

```mermaid
flowchart TD
    Blocks["Scheduled Calendar Blocks for Week"] --> ChronoSort["Sort Chronologically by Start Time"]
    ChronoSort --> OverlapScan["Scan Adjacent Pairs for Overlap:<br/>BlockA.start < BlockB.end AND BlockB.start < BlockA.end"]

    OverlapScan --> ConflictFound{"Overlap Detected?"}
    ConflictFound --> |No Conflict| ValidatedSchedule["Calendar Schedule Clear"]

    ConflictFound --> |Yes| PriorityResolution["Analyze Block Priority:<br/>User Pinned Event vs Auto-Suggested Slot"]
    PriorityResolution --> Preserve["Preserve Pinned / Fixed Event Slot"]
    PriorityResolution --> Replan["Calculate Next Available Contiguous Window"]
    Replan --> Action["Surface Prompt: 'Shift Suggested Block B to 15:30?'"]
```

---

## 🌍 IANA Timezone Recurrence Lifecycle

Study routines are stored as local calendar intent (e.g., "09:00 AM every Monday") paired with an explicit IANA timezone identifier (e.g., `Asia/Kolkata` or `America/New_York`), avoiding DST transition corruption.

### Diagram 18: IANA Timezone Recurrence Expansion Lifecycle

```mermaid
flowchart LR
    LocalIntent["Local Intent:<br/>Start: 09:00 AM (540 min)<br/>Timezone: 'Asia/Kolkata'<br/>Recurrence: [Mon, Wed, Fri]"] --> Materializer["Occurrence Materializer"]

    Materializer --> QueryDate["Target Date: 2026-10-19 (Monday)"]
    QueryDate --> ZoneResolver["IANA Zoneinfo Lookup<br/>Calculate UTC Instant: 03:30:00Z"]
    
    ZoneResolver --> DSTCheck{"DST Transition in Effect?"}
    DSTCheck --> |Yes| AdjustOffset["Adjust UTC offset automatically"]
    DSTCheck --> |No| DirectUTC["Map to absolute UTC timestamp"]

    AdjustOffset & DirectUTC --> DurableOccurrence["Materialized Focus Block Instant"]
```
