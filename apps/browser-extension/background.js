/**
 * StudyLock AI - Chrome/Edge Extension Background Service Worker
 * Ref: StudyLock AI Architecture Specification Section 6.1 & 6.4 (YouTube/Instagram strategy)
 */

const DEFAULT_BLOCKED_DOMAINS = [
  "youtube.com",
  "youtu.be",
  "instagram.com",
  "tiktok.com",
  "twitter.com",
  "x.com",
  "reddit.com",
  "netflix.com"
];

// Initialize storage state
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    isFocusActive: false,
    sessionData: null,
    blockedDomains: DEFAULT_BLOCKED_DOMAINS,
    enforcementState: "ACTIVE"
  });
  console.log("[StudyLock AI] Background worker initialized.");
});

// Update Declarative Net Request rules based on focus state
async function updateEnforcementRules(isFocusActive, customDomains = []) {
  const domains = [...new Set([...DEFAULT_BLOCKED_DOMAINS, ...customDomains])];
  const blockedPageUrl = chrome.runtime.getURL("blocked.html");

  if (!isFocusActive) {
    // Remove all dynamic blocking rules
    const existingRules = await chrome.declarativeNetRequest.getDynamicRules();
    const ruleIds = existingRules.map(r => r.id);
    if (ruleIds.length > 0) {
      await chrome.declarativeNetRequest.updateDynamicRules({
        removeRuleIds: ruleIds,
        addRules: []
      });
    }
    console.log("[StudyLock AI] Distraction rules cleared (Session inactive).");
    return;
  }

  // Construct DNR redirect rules
  const newRules = domains.map((domain, index) => ({
    id: index + 1,
    priority: 1,
    action: {
      type: "redirect",
      redirect: { url: blockedPageUrl }
    },
    condition: {
      urlFilter: `||${domain}`,
      resourceTypes: ["main_frame"]
    }
  }));

  const existingRules = await chrome.declarativeNetRequest.getDynamicRules();
  const existingIds = existingRules.map(r => r.id);

  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: existingIds,
    addRules: newRules
  });

  console.log(`[StudyLock AI] Applied ${newRules.length} dynamic restriction rules.`);
}

// Message listener from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "TOGGLE_FOCUS") {
    chrome.storage.local.get(["isFocusActive", "blockedDomains"], async (data) => {
      const nextState = !data.isFocusActive;
      await chrome.storage.local.set({ isFocusActive: nextState });
      await updateEnforcementRules(nextState, data.blockedDomains || []);
      sendResponse({ status: "success", isFocusActive: nextState });
    });
    return true; // Keep message channel open for async response
  }

  if (message.type === "SYNC_RULES") {
    const { isFocusActive, rules } = message.payload;
    chrome.storage.local.set({ isFocusActive, blockedDomains: rules }, async () => {
      await updateEnforcementRules(isFocusActive, rules);
      sendResponse({ status: "synced" });
    });
    return true;
  }
});
