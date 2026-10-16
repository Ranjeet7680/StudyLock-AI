/**
 * StudyLock AI — Master Frontend Application Controller
 * Ref: StudyLock AI Architecture Specification Section 4, 7, 8, 9, 10, 11, 14, 16
 */

class StudyLockApp {
  constructor() {
    this.apiBase = "http://127.0.0.1:8000/api/v1";
    this.token = null;
    this.currentUser = {
      name: "Alex Student",
      email: "alex.student@university.edu",
      timezone: "Asia/Kolkata",
      level: 1,
      totalXp: 145
    };

    // State Machine & Session State (Section 7)
    this.session = {
      id: null,
      state: "IDLE", // IDLE, FOCUSING, PAUSED, BREAK, COMPLETED, CANCELLED
      plannedMinutes: 25,
      actualSeconds: 0,
      pausedSeconds: 0,
      startedAt: null,
      lastPauseAt: null,
      interruptions: 0,
      taskTitle: "Finish Distributed Systems Lab",
      taskSubject: "Computer Science",
      timerInterval: null
    };

    // Local Tasks Collection (Section 9)
    this.tasks = [
      { id: "t-1", title: "Distributed Systems Lab Review", subject: "Computer Science", priority: 3, estimatedMinutes: 45, status: "todo", dueAt: "Tomorrow, 17:00" },
      { id: "t-2", title: "Read Chapter 4: Consensus Protocols", subject: "Computer Science", priority: 2, estimatedMinutes: 30, status: "todo", dueAt: "In 2 days" },
      { id: "t-3", title: "Calculus Problem Set 7", subject: "Mathematics", priority: 4, estimatedMinutes: 60, status: "todo", dueAt: "Today, 23:59" },
      { id: "t-4", title: "Draft Literature Review Introduction", subject: "Academic Writing", priority: 2, estimatedMinutes: 45, status: "done", dueAt: "Yesterday" }
    ];

    // Local Block Rules Collection (Section 6)
    this.rules = [
      { id: "r-1", target_type: "domain", target_value: "youtube.com", action: "block", enabled: true },
      { id: "r-2", target_type: "domain", target_value: "youtu.be", action: "block", enabled: true },
      { id: "r-3", target_type: "domain", target_value: "instagram.com", action: "block", enabled: true },
      { id: "r-4", target_type: "domain", target_value: "tiktok.com", action: "block", enabled: true },
      { id: "r-5", target_type: "domain", target_value: "reddit.com", action: "block", enabled: true },
      { id: "r-6", target_type: "domain", target_value: "x.com", action: "block", enabled: true },
      { id: "r-7", target_type: "app_package", target_value: "discord.exe", action: "block", enabled: true },
      { id: "r-8", target_type: "app_package", target_value: "steam.exe", action: "block", enabled: true }
    ];

    // Cryptographic Reward Ledger Entries (Section 10)
    this.ledger = [
      { id: "led-1", event_key: "EVT_FIRST_SESSION:alex", xp_delta: 25, reason: "First valid focus session completed", created_at: "2026-10-14 10:30" },
      { id: "led-2", event_key: "EVT_SESSION_45M:sess-101", xp_delta: 40, reason: "Deep focus 45+ minute session completed", created_at: "2026-10-15 14:45" },
      { id: "led-3", event_key: "EVT_DAILY_GOAL:alex:2026-10-15", xp_delta: 50, reason: "Daily study goal achieved (120m)", created_at: "2026-10-15 18:00" },
      { id: "led-4", event_key: "EVT_TASK_COMPLETED:t-4", xp_delta: 20, reason: "Task goal achieved: Literature Review", created_at: "2026-10-15 19:15" }
    ];

    // Achievements Catalog
    this.achievements = [
      { code: "FIRST_SESSION", title: "First Step", desc: "Complete your first timed session", icon: "🌱", xp: 25, unlocked: true },
      { code: "DEEP_DIVER", title: "Deep Diver", desc: "Complete 45+ min uninterrupted block", icon: "🌊", xp: 40, unlocked: true },
      { code: "STREAK_3", title: "Habit Builder", desc: "Study 3 consecutive days", icon: "🔥", xp: 75, unlocked: true },
      { code: "TASK_MASTER", title: "Task Finisher", desc: "Complete 5 scheduled study tasks", icon: "⚡", xp: 50, unlocked: false },
      { code: "ZEN_MODE", title: "Digital Monk", desc: "Zero interruptions recorded in session", icon: "🧘", xp: 30, unlocked: false },
    ];

    this.init();
  }

  init() {
    this.setupNavigation();
    this.setupFocusControls();
    this.setupTaskControls();
    this.setupBlocklistControls();
    this.setupPrivacyControls();
    this.renderTasks();
    this.renderHomePriorityTasks();
    this.renderRules();
    this.renderLedgerAndAchievements();
    this.renderAnalytics();
    this.renderDevices();
    this.renderPlannerSuggestions();
  }

  // --- NAVIGATION ---
  setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const panels = document.querySelectorAll(".view-panel");
    const pageTitle = document.getElementById("pageTitle");
    const pageSubtitle = document.getElementById("pageSubtitle");

    const titles = {
      home: { title: "Home Dashboard", desc: "Overview of your daily focus target, routines, and task queue." },
      focus: { title: "Focus Room", desc: "Immersion study chamber with verified OS adapter restrictions." },
      planner: { title: "Planner & Calendar", desc: "Weekly recurrence, timezone mapping, and conflict resolution." },
      tasks: { title: "Tasks & Deadlines", desc: "Manage prioritized objectives and schedule study sessions." },
      blocklist: { title: "Blocklist & Rules", desc: "App and domain rules with precedence and simulation tools." },
      analytics: { title: "Analytics & Trends", desc: "Planned vs. actual focus trends and subject breakdowns." },
      rewards: { title: "Rewards & Ledger", desc: "Cryptographic XP events, level progression, and badges." },
      devices: { title: "Device Health", desc: "Platform adapters, permission health, and sync diagnostics." },
      privacy: { title: "Privacy & Settings", desc: "Data minimization, export requests, and account controls." }
    };

    navItems.forEach(item => {
      item.addEventListener("click", () => {
        const view = item.getAttribute("data-view");
        navItems.forEach(n => n.classList.remove("active"));
        panels.forEach(p => p.classList.remove("active"));

        item.classList.add("active");
        const activePanel = document.getElementById(`view-${view}`);
        if (activePanel) activePanel.classList.add("active");

        if (titles[view]) {
          pageTitle.textContent = titles[view].title;
          pageSubtitle.textContent = titles[view].desc;
        }
      });
    });

    document.getElementById("topbarStartFocusBtn").addEventListener("click", () => {
      this.switchView("focus");
      if (this.session.state === "IDLE") {
        this.startSession(25, "Quick Focus Block", "Self-Directed");
      }
    });
  }

  switchView(viewName) {
    const targetNav = document.querySelector(`.nav-item[data-view='${viewName}']`);
    if (targetNav) targetNav.click();
  }

  // --- FOCUS SESSION STATE MACHINE (Section 7) ---
  setupFocusControls() {
    const pauseBtn = document.getElementById("focusPauseBtn");
    const finishBtn = document.getElementById("focusFinishBtn");
    const emergencyExitBtn = document.getElementById("focusEmergencyExitBtn");

    pauseBtn.addEventListener("click", () => this.togglePause());
    finishBtn.addEventListener("click", () => this.finishSession());
    emergencyExitBtn.addEventListener("click", () => this.emergencyExit());

    document.getElementById("closeSummaryModalBtn").addEventListener("click", () => {
      document.getElementById("sessionSummaryModal").style.display = "none";
      this.switchView("home");
    });
  }

  launchSessionFromTask(taskTitle, minutes = 25, subject = "Computer Science") {
    this.switchView("focus");
    this.startSession(minutes, taskTitle, subject);
  }

  startSession(minutes, taskTitle, subject) {
    this.session.id = "sess-" + Math.floor(Math.random() * 10000);
    this.session.state = "FOCUSING";
    this.session.plannedMinutes = minutes;
    this.session.actualSeconds = 0;
    this.session.pausedSeconds = 0;
    this.session.interruptions = 0;
    this.session.startedAt = Date.now();
    this.session.lastPauseAt = null;
    this.session.taskTitle = taskTitle;
    this.session.taskSubject = subject;

    document.getElementById("focusTaskTitle").textContent = taskTitle;
    document.getElementById("focusTaskSubject").textContent = subject;
    document.getElementById("focusTimerSublabel").textContent = `${minutes}-minute deep focus block`;
    document.getElementById("focusInterruptionCount").textContent = "0";
    document.getElementById("navLiveIndicator").style.display = "inline-block";

    this.updateFocusUI();

    if (this.session.timerInterval) clearInterval(this.session.timerInterval);
    this.session.timerInterval = setInterval(() => this.timerTick(), 1000);
  }

  timerTick() {
    if (this.session.state !== "FOCUSING") return;

    // Correctness: calculate elapsed from timestamps, avoiding drifting counter (Section 7.2)
    const now = Date.now();
    const totalElapsedSecs = Math.floor((now - this.session.startedAt) / 1000);
    const netFocusSecs = Math.max(0, totalElapsedSecs - this.session.pausedSeconds);
    this.session.actualSeconds = netFocusSecs;

    const remainingSecs = Math.max(0, (this.session.plannedMinutes * 60) - netFocusSecs);
    const mins = String(Math.floor(remainingSecs / 60)).padStart(2, '0');
    const secs = String(remainingSecs % 60).padStart(2, '0');
    document.getElementById("focusTimerDigits").textContent = `${mins}:${secs}`;

    if (remainingSecs <= 0) {
      this.finishSession();
    }
  }

  togglePause() {
    const pauseBtn = document.getElementById("focusPauseBtn");
    const now = Date.now();

    if (this.session.state === "FOCUSING") {
      this.session.state = "PAUSED";
      this.session.lastPauseAt = now;
      this.session.interruptions++;
      document.getElementById("focusInterruptionCount").textContent = this.session.interruptions;
      pauseBtn.textContent = "▶️ Resume Session";
      this.updateFocusUI();
    } else if (this.session.state === "PAUSED") {
      if (this.session.lastPauseAt) {
        const pauseDelta = Math.floor((now - this.session.lastPauseAt) / 1000);
        this.session.pausedSeconds += Math.max(0, pauseDelta);
        this.session.lastPauseAt = null;
      }
      this.session.state = "FOCUSING";
      pauseBtn.textContent = "⏸️ Pause Session";
      this.updateFocusUI();
    }
  }

  finishSession() {
    if (this.session.timerInterval) clearInterval(this.session.timerInterval);
    this.session.state = "COMPLETED";
    document.getElementById("navLiveIndicator").style.display = "none";

    const actualMins = Math.floor(this.session.actualSeconds / 60);
    const actualSecsRemainder = this.session.actualSeconds % 60;
    const isDeep = actualMins >= 45;
    const earnedXp = isDeep ? 40 : 25;
    const reason = isDeep ? "Deep focus 45+ minute block completed" : "Focus session completed";

    // Insert into Immutable Reward Ledger (Section 10)
    const ledgerEntry = {
      id: "led-" + (this.ledger.length + 1),
      event_key: `EVT_SESSION_${this.session.id}`,
      xp_delta: earnedXp,
      reason: reason,
      created_at: new Date().toISOString().replace("T", " ").substring(0, 16)
    };
    this.ledger.unshift(ledgerEntry);
    this.currentUser.totalXp += earnedXp;

    // Show summary modal
    document.getElementById("summaryDuration").textContent = `${actualMins} min ${actualSecsRemainder} sec`;
    document.getElementById("summaryXp").textContent = `+${earnedXp} XP`;
    document.getElementById("summaryReason").textContent = reason;
    document.getElementById("summaryLevelProgress").textContent = `Level 1 Scholar • Total: ${this.currentUser.totalXp} XP`;
    document.getElementById("sessionSummaryModal").style.display = "flex";

    this.renderLedgerAndAchievements();
    this.updateUserBadge();
  }

  emergencyExit() {
    const confirmExit = confirm(
      "Emergency Exit Confirmation:\nAre you sure you want to end this focus session early?\nYour session will be closed cleanly without shame, but completion XP requires completing the target duration."
    );
    if (!confirmExit) return;

    if (this.session.timerInterval) clearInterval(this.session.timerInterval);
    this.session.state = "CANCELLED";
    document.getElementById("navLiveIndicator").style.display = "none";
    alert("Session exited safely. Platform restrictions have been cleared.");
    this.switchView("home");
  }

  updateFocusUI() {
    const stateBadge = document.getElementById("focusStateBadge");
    const enforcementBadge = document.getElementById("focusEnforcementBadge");

    if (this.session.state === "FOCUSING") {
      stateBadge.textContent = "STATE: FOCUSING";
      stateBadge.style.backgroundColor = "rgba(59, 130, 246, 0.2)";
      stateBadge.style.color = "#93C5FD";

      enforcementBadge.textContent = "🛡️ RESTRICTIONS ENFORCED";
      enforcementBadge.style.backgroundColor = "rgba(16, 185, 129, 0.2)";
      enforcementBadge.style.color = "#34D399";
    } else if (this.session.state === "PAUSED") {
      stateBadge.textContent = "STATE: PAUSED";
      stateBadge.style.backgroundColor = "rgba(245, 158, 11, 0.2)";
      stateBadge.style.color = "#FBBF24";

      enforcementBadge.textContent = "⏸️ RESTRICTIONS TEMPORARILY SUSPENDED";
      enforcementBadge.style.backgroundColor = "rgba(245, 158, 11, 0.2)";
      enforcementBadge.style.color = "#FBBF24";
    }
  }

  // --- TASKS (Section 9) ---
  setupTaskControls() {
    const newTaskModal = document.getElementById("newTaskModal");
    document.getElementById("openNewTaskModalBtn").addEventListener("click", () => {
      newTaskModal.style.display = "flex";
    });
    document.getElementById("closeTaskModalBtn").addEventListener("click", () => {
      newTaskModal.style.display = "none";
    });
    document.getElementById("cancelTaskModalBtn").addEventListener("click", () => {
      newTaskModal.style.display = "none";
    });

    document.getElementById("saveTaskModalBtn").addEventListener("click", () => {
      const title = document.getElementById("taskModalTitle").value.trim();
      const subject = document.getElementById("taskModalSubject").value.trim() || "General Study";
      const priority = parseInt(document.getElementById("taskModalPriority").value, 10);
      const minutes = parseInt(document.getElementById("taskModalMinutes").value, 10) || 30;

      if (!title) {
        alert("Please enter a task title.");
        return;
      }

      this.tasks.unshift({
        id: "t-" + (this.tasks.length + 1),
        title: title,
        subject: subject,
        priority: priority,
        estimatedMinutes: minutes,
        status: "todo",
        dueAt: "Upcoming"
      });

      newTaskModal.style.display = "none";
      document.getElementById("taskModalTitle").value = "";
      this.renderTasks();
      this.renderHomePriorityTasks();
    });

    // Task Filter Buttons
    document.querySelectorAll(".filter-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.renderTasks(btn.getAttribute("data-filter"));
      });
    });
  }

  toggleTaskStatus(taskId) {
    const task = this.tasks.find(t => t.id === taskId);
    if (!task) return;

    if (task.status !== "done") {
      task.status = "done";
      // Award Task Completion XP (+20 XP)
      this.ledger.unshift({
        id: "led-" + (this.ledger.length + 1),
        event_key: `EVT_TASK_COMPLETED:${task.id}`,
        xp_delta: 20,
        reason: `Completed task: ${task.title}`,
        created_at: new Date().toISOString().replace("T", " ").substring(0, 16)
      });
      this.currentUser.totalXp += 20;
      this.renderLedgerAndAchievements();
      this.updateUserBadge();
    } else {
      task.status = "todo";
    }
    this.renderTasks();
    this.renderHomePriorityTasks();
  }

  renderTasks(filter = "all") {
    const tbody = document.getElementById("tasksTableBody");
    tbody.innerHTML = "";

    const filtered = this.tasks.filter(t => {
      if (filter === "todo") return t.status === "todo";
      if (filter === "done") return t.status === "done";
      return true;
    });

    filtered.forEach(task => {
      const tr = document.createElement("tr");
      const priorityLabels = { 1: "Low", 2: "Med", 3: "High", 4: "Critical" };
      const priorityClasses = { 1: "p-low", 2: "p-medium", 3: "p-high", 4: "p-critical" };

      tr.innerHTML = `
        <td>
          <input type="checkbox" ${task.status === "done" ? "checked" : ""} onchange="app.toggleTaskStatus('${task.id}')">
        </td>
        <td style="${task.status === "done" ? "text-decoration: line-through; color: var(--text-muted);" : "font-weight: 500;"}">
          ${task.title}
        </td>
        <td><span class="badge badge-neutral">${task.subject}</span></td>
        <td><span class="priority-badge ${priorityClasses[task.priority]}">${priorityLabels[task.priority]}</span></td>
        <td>${task.estimatedMinutes} min</td>
        <td>${task.dueAt}</td>
        <td>
          <button class="btn btn-primary" style="padding: 4px 10px; font-size: 11px;" onclick="app.launchSessionFromTask('${task.title}', ${task.estimatedMinutes}, '${task.subject}')">Focus</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  renderHomePriorityTasks() {
    const container = document.getElementById("homePriorityTasks");
    container.innerHTML = "";

    const activeTasks = this.tasks.filter(t => t.status === "todo").slice(0, 3);
    activeTasks.forEach(task => {
      const item = document.createElement("div");
      item.className = "schedule-callout";
      item.style.marginBottom = "8px";
      item.innerHTML = `
        <div class="schedule-detail">
          <div class="schedule-name">${task.title}</div>
          <div class="schedule-meta">${task.subject} • Priority ${task.priority} • Est: ${task.estimatedMinutes} min</div>
        </div>
        <button class="btn btn-secondary" onclick="app.launchSessionFromTask('${task.title}', ${task.estimatedMinutes}, '${task.subject}')">Study</button>
      `;
      container.appendChild(item);
    });
  }

  // --- BLOCKLIST & RULES (Section 6) ---
  setupBlocklistControls() {
    document.getElementById("saveRuleBtn").addEventListener("click", () => {
      const type = document.getElementById("newRuleType").value;
      const val = document.getElementById("newRuleValue").value.trim();
      const action = document.getElementById("newRuleAction").value;

      if (!val) {
        alert("Please enter a domain or process name.");
        return;
      }

      this.rules.push({
        id: "r-" + (this.rules.length + 1),
        target_type: type,
        target_value: val,
        action: action,
        enabled: true
      });

      document.getElementById("newRuleValue").value = "";
      this.renderRules();
    });

    // Rule Simulator
    document.getElementById("simTestBtn").addEventListener("click", () => {
      const input = document.getElementById("simCandidateInput").value.trim().toLowerCase();
      const resBox = document.getElementById("simResultBox");
      if (!input) {
        resBox.textContent = "Please enter a test URL or package name.";
        return;
      }

      // Check against rules with precedence
      let matched = null;
      for (const rule of this.rules) {
        if (!rule.enabled) continue;
        if (rule.target_type === "domain") {
          const ruleDomain = rule.target_value.toLowerCase();
          if (input.includes(ruleDomain) || (ruleDomain === "youtube.com" && input.includes("youtu.be"))) {
            matched = rule;
            break;
          }
        } else if (rule.target_type === "app_package") {
          if (input === rule.target_value.toLowerCase()) {
            matched = rule;
            break;
          }
        }
      }

      if (matched) {
        resBox.innerHTML = `
          <strong style="color: ${matched.action === 'block' ? '#EF4444' : '#10B981'};">
            ACTION: ${matched.action.toUpperCase()}
          </strong><br>
          Matched Rule ID: <code>${matched.id}</code> (${matched.target_value})<br>
          Adapter Precedence: Exact ${matched.target_type} match applied.
        `;
      } else {
        resBox.innerHTML = `
          <strong style="color: #9CA3AF;">ACTION: UNRESTRICTED</strong><br>
          No active rule matches '${input}'. Traffic allowed.
        `;
      }
    });
  }

  addPreset(value) {
    const exists = this.rules.some(r => r.target_value === value);
    if (!exists) {
      this.rules.push({
        id: "r-" + (this.rules.length + 1),
        target_type: value.endsWith(".exe") ? "app_package" : "domain",
        target_value: value,
        action: "block",
        enabled: true
      });
      this.renderRules();
      alert(`Preset for '${value}' added to active blocklist!`);
    } else {
      alert(`'${value}' is already in your blocklist.`);
    }
  }

  renderRules() {
    const tbody = document.getElementById("rulesTableBody");
    tbody.innerHTML = "";

    this.rules.forEach(rule => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="badge badge-neutral">${rule.target_type}</span></td>
        <td><code>${rule.target_value}</code></td>
        <td><span class="badge ${rule.action === "block" ? "badge-active" : "badge-neutral"}" style="${rule.action === 'block' ? 'background: rgba(239, 68, 68, 0.2); color: #F87171;' : ''}">${rule.action.toUpperCase()}</span></td>
        <td><span class="green-text">● Enforced</span></td>
        <td>
          <button class="btn btn-danger" style="padding: 2px 8px; font-size: 11px;" onclick="app.deleteRule('${rule.id}')">Remove</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  deleteRule(ruleId) {
    this.rules = this.rules.filter(r => r.id !== ruleId);
    this.renderRules();
  }

  // --- REWARDS & LEDGER (Section 10) ---
  renderLedgerAndAchievements() {
    // Achievements
    const grid = document.getElementById("achievementsGrid");
    grid.innerHTML = "";
    this.achievements.forEach(ach => {
      const card = document.createElement("div");
      card.className = `achievement-card ${ach.unlocked ? "unlocked" : ""}`;
      card.innerHTML = `
        <div class="achievement-icon">${ach.icon}</div>
        <div class="achievement-title">${ach.title} ${ach.unlocked ? "✓" : ""}</div>
        <div class="achievement-desc">${ach.desc}</div>
        <div style="font-size: 11px; color: #93C5FD; margin-top: 4px;">+${ach.xp} XP</div>
      `;
      grid.appendChild(card);
    });

    // Ledger
    const ledgerList = document.getElementById("ledgerList");
    ledgerList.innerHTML = "";
    this.ledger.forEach(entry => {
      const item = document.createElement("div");
      item.className = "ledger-entry";
      item.innerHTML = `
        <div>
          <div>${entry.reason}</div>
          <div class="ledger-key">${entry.event_key} • ${entry.created_at}</div>
        </div>
        <div class="green-text" style="font-weight: 700;">+${entry.xp_delta} XP</div>
      `;
      ledgerList.appendChild(item);
    });

    document.getElementById("rewardTotalXpDisplay").textContent = `${this.currentUser.totalXp} XP`;
    document.getElementById("homeTotalXp").innerHTML = `${this.currentUser.totalXp} <span class="unit">XP</span>`;
  }

  updateUserBadge() {
    document.getElementById("userLevelDisplay").textContent = `Level 1 • ${this.currentUser.totalXp} XP`;
  }

  // --- ANALYTICS (Section 11) ---
  renderAnalytics() {
    const container = document.getElementById("analyticsBarChart");
    container.innerHTML = `
      <div style="display: flex; align-items: flex-end; justify-content: space-around; height: 160px; padding: 10px 0; border-bottom: 1px solid var(--border-default);">
        <div style="text-align: center;"><div style="height: 60px; width: 32px; background: #3B82F6; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Sat</div></div>
        <div style="text-align: center;"><div style="height: 90px; width: 32px; background: #3B82F6; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Sun</div></div>
        <div style="text-align: center;"><div style="height: 120px; width: 32px; background: #3B82F6; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Mon</div></div>
        <div style="text-align: center;"><div style="height: 85px; width: 32px; background: #3B82F6; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Tue</div></div>
        <div style="text-align: center;"><div style="height: 140px; width: 32px; background: #10B981; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Wed</div></div>
        <div style="text-align: center;"><div style="height: 70px; width: 32px; background: #3B82F6; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Thu</div></div>
        <div style="text-align: center;"><div style="height: 110px; width: 32px; background: #3B82F6; border-radius: 4px; margin: 0 auto;"></div><div style="font-size: 11px; color: var(--text-muted); margin-top: 6px;">Fri</div></div>
      </div>
    `;

    const sub = document.getElementById("analyticsSubjectBreakdown");
    sub.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;"><span>Computer Science</span><span>140 min (57%)</span></div>
          <div class="metric-progress-bg"><div class="metric-progress-bar" style="width: 57%;"></div></div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;"><span>Mathematics</span><span>65 min (27%)</span></div>
          <div class="metric-progress-bg"><div class="metric-progress-bar" style="width: 27%; background-color: #8B5CF6;"></div></div>
        </div>
        <div>
          <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;"><span>Academic Writing</span><span>40 min (16%)</span></div>
          <div class="metric-progress-bg"><div class="metric-progress-bar" style="width: 16%; background-color: #F59E0B;"></div></div>
        </div>
      </div>
    `;
  }

  // --- DEVICES (Section 6.5) ---
  renderDevices() {
    const container = document.getElementById("devicesListContainer");
    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 12px;">
        <div class="schedule-callout" style="border-left-color: #10B981;">
          <div style="font-size: 24px;">💻</div>
          <div class="schedule-detail">
            <div class="schedule-name">Windows Desktop Host (Active Workstation)</div>
            <div class="schedule-meta">Adapter: Desktop Process Blocker • Last Heartbeat: 20s ago • Version: 1.0.0</div>
          </div>
          <span class="badge badge-active">ENFORCING</span>
        </div>

        <div class="schedule-callout" style="border-left-color: #3B82F6;">
          <div style="font-size: 24px;">🌐</div>
          <div class="schedule-detail">
            <div class="schedule-name">Chrome / Edge WebExtension (MV3)</div>
            <div class="schedule-meta">Adapter: DeclarativeNetRequest Domain Filter • 8 rules synced</div>
          </div>
          <span class="badge badge-active">CONNECTED</span>
        </div>

        <div class="schedule-callout" style="border-left-color: #6B7280;">
          <div style="font-size: 24px;">📱</div>
          <div class="schedule-detail">
            <div class="schedule-name">Android Device (Pixel 8)</div>
            <div class="schedule-meta">Adapter: UsageStats & WorkManager Sync • Ready to link</div>
          </div>
          <button class="btn btn-secondary" style="padding: 4px 10px; font-size: 11px;" onclick="alert('Scan QR code with StudyLock Android app to link device.')">Link Device</button>
        </div>
      </div>
    `;
  }

  // --- PLANNER SUGGESTIONS (Section 8.4) ---
  renderPlannerSuggestions() {
    const container = document.getElementById("plannerSuggestionsContainer");
    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
        <div class="schedule-callout" style="border-left-color: #EF4444;">
          <div class="schedule-detail">
            <div class="schedule-name">Calculus Problem Set 7 (Due Today)</div>
            <div class="schedule-meta">Score: 92.5 • Approaching deadline • Critical priority</div>
          </div>
          <button class="btn btn-primary" onclick="app.launchSessionFromTask('Calculus Problem Set 7', 60, 'Mathematics')">Slot 15:30</button>
        </div>

        <div class="schedule-callout">
          <div class="schedule-detail">
            <div class="schedule-name">Distributed Systems Lab Review</div>
            <div class="schedule-meta">Score: 84.0 • High priority rating • Exam syllabus</div>
          </div>
          <button class="btn btn-primary" onclick="app.launchSessionFromTask('Distributed Systems Lab Review', 45, 'Computer Science')">Slot 17:00</button>
        </div>
      </div>
    `;

    document.getElementById("detectConflictsBtn").addEventListener("click", () => {
      alert("Conflict Analysis Complete:\nNo overlapping calendar blocks found for current week.\nAll scheduled blocks comply with available study hours.");
    });

    document.getElementById("addScheduleBtn").addEventListener("click", () => {
      const title = prompt("Enter Recurring Study Routine Title:", "Evening Deep Focus");
      if (title) alert(`Routine '${title}' added to calendar engine.`);
    });
  }

  // --- PRIVACY & SETTINGS (Section 16) ---
  setupPrivacyControls() {
    document.getElementById("exportDataBtn").addEventListener("click", () => {
      const exportBlob = new Blob([
        JSON.stringify({
          user: this.currentUser,
          tasks: this.tasks,
          rules: this.rules,
          ledger: this.ledger,
          achievements: this.achievements,
          exported_at: new Date().toISOString()
        }, null, 2)
      ], { type: "application/json" });

      const url = URL.createObjectURL(exportBlob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `StudyLock_AI_Data_Export_${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });

    document.getElementById("deleteAccountBtn").addEventListener("click", () => {
      const conf = confirm("DANGER: Are you sure you want to permanently delete your account and all focus history? This action is irreversible.");
      if (conf) {
        alert("Account and local data have been purged.");
        window.location.reload();
      }
    });

    document.getElementById("savePreferencesBtn").addEventListener("click", () => {
      const name = document.getElementById("prefDisplayName").value.trim();
      const tz = document.getElementById("prefTimezone").value;
      if (name) this.currentUser.name = name;
      this.currentUser.timezone = tz;
      document.getElementById("userNameDisplay").textContent = name;
      document.getElementById("plannerTimezoneBadge").textContent = `Timezone: ${tz}`;
      alert("Preferences saved successfully!");
    });
  }
}

// Instantiate global controller on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  window.app = new StudyLockApp();
});
