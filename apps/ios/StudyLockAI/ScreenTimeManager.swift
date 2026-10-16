//
//  ScreenTimeManager.swift
//  StudyLockAI
//  Ref: StudyLock AI Architecture Specification Section 5.2, 6.1, 6.4 (iOS ScreenTime Integration)
//

import Foundation
import FamilyControls
import ManagedSettings
import DeviceActivity

enum IOSEnforcementState: String {
    case notConfigured = "NOT_CONFIGURED"
    case permissionRequired = "PERMISSION_REQUIRED"
    case active = "ACTIVE"
    case failed = "FAILED"
}

@MainActor
class ScreenTimeManager: ObservableObject {
    static let shared = ScreenTimeManager()
    
    @Published var enforcementState: IOSEnforcementState = .notConfigured
    @Published var activitySelection = FamilyActivitySelection()
    
    private let store = ManagedSettingsStore()
    
    func requestAuthorization() async {
        do {
            try await AuthorizationCenter.shared.requestAuthorization(for: .individual)
            self.enforcementState = .active
        } catch {
            print("[StudyLock AI iOS] FamilyControls authorization denied: \(error)")
            self.enforcementState = .permissionRequired
        }
    }
    
    func applyShields() {
        guard enforcementState == .active else { return }
        // Apply shields to selected applications and categories
        store.shield.applications = activitySelection.applicationTokens
        store.shield.applicationCategories = ShieldSettings.ActivityCategoryPolicy.specific(activitySelection.categoryTokens)
        print("[StudyLock AI iOS] ManagedSettings shields applied.")
    }
    
    func clearShields() {
        store.shield.applications = nil
        store.shield.applicationCategories = nil
        print("[StudyLock AI iOS] ManagedSettings shields cleared.")
    }
}
