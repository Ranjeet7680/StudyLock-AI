# 04. Rule Engine & Precedence

StudyLock AI utilizes an explicit, deterministic precedence engine so learners understand why a website or application was blocked or allowed.

---

## ⚖️ Precedence Resolution Hierarchy

When candidate URLs or process names match multiple rules, specificity and allow-overrides resolve deterministically.

### Diagram 14: Rule Precedence Resolution Hierarchy

```mermaid
flowchart TD
    Candidate["Candidate Destination (URL, Host, or Executable)"] --> Eval["Evaluate All Active Enabled Rules"]

    Eval --> Level1{"Specific URL Pattern Match?<br/>(e.g., *youtube.com/c/3blue1brown*)"}
    Level1 --> |ALLOW Rule| Allow1["Action: ALLOW (Educational Channel Override)"]
    Level1 --> |BLOCK Rule| Block1["Action: BLOCK (Specific URL Pattern Block)"]
    Level1 --> |No URL Match| Level2{"Exact Domain / App Package Match?<br/>(e.g., youtube.com, discord.exe)"}

    Level2 --> |ALLOW Rule| Allow2["Action: ALLOW (Domain Allowlist)"]
    Level2 --> |BLOCK Rule| Block2["Action: BLOCK (Domain / Process Block)"]
    Level2 --> |No Domain Match| Level3{"Category Match?<br/>(e.g., social_media, gaming)"}

    Level3 --> |ALLOW Rule| Allow3["Action: ALLOW (Category Exception)"]
    Level3 --> |BLOCK Rule| Block3["Action: BLOCK (Category Block)"]
    Level3 --> |No Match| DefaultAction["Action: UNRESTRICTED (Allow)"]
```

---

## 📺 YouTube & Instagram Distraction Strategy

Popular platforms utilize diverse hostnames, mobile subdomains, and short-links. StudyLock normalizes and canonicalizes destinations.

### Diagram 15: YouTube & Instagram Distraction Matching Workflow

```mermaid
flowchart LR
    RawURL["Raw Target URL Input"] --> Norm["Domain Normalization<br/>(Strip protocol, www, port & path)"]

    Norm --> MatchRules{"Check Canonical Host"}

    MatchRules --> |youtube.com / youtu.be / m.youtube.com| YTBlock["Matched Canonical: YOUTUBE<br/>Status: Intercept Main Frame"]
    MatchRules --> |instagram.com / m.instagram.com / ig.me| IGBlock["Matched Canonical: INSTAGRAM<br/>Status: Intercept Main Frame"]
    MatchRules --> |Other Domains| GenMatch["Standard Suffix & Wildcard Match"]

    YTBlock & IGBlock & GenMatch --> Decision["Return Decision to Platform Adapter"]
```
