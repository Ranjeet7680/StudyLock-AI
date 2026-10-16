# 03. Platform Enforcement Adapters

StudyLock AI interfaces with operating system restriction primitives through a normalized adapter contract. The domain never assumes parity across operating systems.

---

## 🧩 Platform Adapter Abstraction

Each platform adapter implements capability checks, rule application, pause handling, and health reporting.

### Diagram 9: Platform Adapter Abstraction Layer

```mermaid
classDiagram
    class EnforcementState {
        <<enumeration>>
        NOT_CONFIGURED
        PERMISSION_REQUIRED
        APPLYING
        ACTIVE
        PARTIAL
        FAILED
    }

    class IPlatformBlockerAdapter {
        <<interface>>
        +checkCapabilities() EnforcementState
        +applyRestrictions(rules: List~BlockRule~) bool
        +pauseRestrictions() void
        +clearRestrictions() void
        +reportEnforcementStatus() EnforcementReport
    }

    class WebExtensionAdapter {
        +declarativeNetRequestRules
        +applyRestrictions()
        +redirectBlockedPage()
    }

    class DesktopDaemonAdapter {
        +processScanner
        +terminateOrSuspendProcess()
        +sendHeartbeat()
    }

    class AndroidPlatformAdapter {
        +usageStatsManager
        +accessibilityService
        +foregroundServiceNotification()
    }

    class IOSPlatformAdapter {
        +managedSettingsStore
        +familyActivitySelection
        +applyShields()
    }

    IPlatformBlockerAdapter <|.. WebExtensionAdapter
    IPlatformBlockerAdapter <|.. DesktopDaemonAdapter
    IPlatformBlockerAdapter <|.. AndroidPlatformAdapter
    IPlatformBlockerAdapter <|.. IOSPlatformAdapter
    IPlatformBlockerAdapter --> EnforcementState
```

---

## 🌐 Chrome / Edge WebExtension (Manifest V3)

The browser extension uses `chrome.declarativeNetRequest` to intercept network requests at the engine level without executing intrusive content-script injections.

### Diagram 10: Chrome/Edge MV3 DeclarativeNetRequest Filter Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student as 🧑‍🎓 Student
    participant Browser as 🌐 Chrome / Edge
    participant DNR as 🛡️ DeclarativeNetRequest Engine
    participant Ext as 🧩 StudyLock MV3 Background Worker
    participant Page as 🛑 blocked.html (Calm Screen)

    Ext->>DNR: updateDynamicRules(addRules=[youtube.com, instagram.com])
    Student->>Browser: Enters "https://www.youtube.com/watch?v=..."
    Browser->>DNR: Check URL match against dynamic rules
    DNR-->>Browser: Action: Redirect to chrome-extension://<id>/blocked.html
    Browser->>Page: Render Inspiring Deep Work Notice
    Note over Page: "Deep Focus Active. Return to your study task."
```

---

## 🤖 Android Native Integration (Kotlin + Room + Compose)

On Android, the companion app combines a persistent foreground notification service with `UsageStatsManager` and Room database.

### Diagram 11: Android UsageStats & Foreground Service Architecture

```mermaid
flowchart TD
    Start["User starts session on Android"] --> Service["Start FocusSessionService<br/>(START_STICKY Foreground Service)"]
    Service --> Notif["Display Persistent Ongoing Notification<br/>(High Priority Channel)"]
    Service --> CheckPerm{"Check AppOps<br/>OPSTR_GET_USAGE_STATS"}

    CheckPerm --> |Permission Granted| Adapter["Activate AndroidBlockingAdapter<br/>Status: ACTIVE"]
    CheckPerm --> |Permission Missing| Prompt["Launch ACTION_USAGE_ACCESS_SETTINGS<br/>Status: PERMISSION_REQUIRED"]

    Adapter --> Poller["Periodically inspect foreground task<br/>(UsageStatsManager)"]
    Poller --> Distract{"Matches Blacklist?<br/>(YouTube / Instagram / TikTok)"}
    Distract --> |Yes| Intercept["Launch StudyLock Focus Screen Overlay"]
    Distract --> |No| Pass["Allow app to run"]
```

---

## 🖥️ Windows & macOS Desktop Daemon Helper

The desktop helper runs as a lightweight daemon inspecting foreground processes and reporting health telemetry to the StudyLock API.

### Diagram 12: Windows Desktop Daemon Process Scan & Heartbeat Loop

```mermaid
flowchart TD
    Init["Launch Desktop Helper (helper.py)"] --> Reg["Register Device with API (/api/v1/devices)"]
    Reg --> Loop["Start 5-Second Monitoring Loop"]

    Loop --> ProcessScan["Scan Running Processes via OS API<br/>(tasklist / ps -e)"]
    ProcessScan --> MatchCheck{"Matches Blacklist?<br/>(discord.exe, steam.exe, games)"}

    MatchCheck --> |Distraction Found| LogWarning["Log Distraction Detected Warning"]
    MatchCheck --> |Clean| Continue["All clear"]

    LogWarning & Continue --> Heartbeat["Send Heartbeat & Enforcement Report<br/>POST /api/v1/devices/{id}/enforcement-report"]
    Heartbeat --> Sleep["Sleep 5s"]
    Sleep --> Loop
```

---

## 🍎 iOS Screen Time & ManagedSettings Integration

On iOS, StudyLock utilizes Apple's official `FamilyControls` and `ManagedSettings` frameworks.

### Diagram 13: iOS Screen Time FamilyControls Shield Architecture

```mermaid
flowchart LR
    Auth["AuthorizationCenter.shared<br/>.requestAuthorization(for: .individual)"] --> Granted{"Authorization<br/>Granted?"}
    
    Granted --> |Yes| Store["ManagedSettingsStore()"]
    Granted --> |No| Err["Status: PERMISSION_REQUIRED"]

    Store --> Apply["store.shield.applications = activitySelection.applicationTokens<br/>store.shield.applicationCategories = .specific(...)"]
    Apply --> ShieldActive["iOS Native Shield Displayed Over Distracting Apps"]
    
    ShieldActive --> Clear["On Session Finish:<br/>store.shield.applications = nil"]
```
