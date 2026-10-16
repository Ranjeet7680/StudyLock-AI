//
//  FocusRoomView.swift
//  StudyLockAI
//  Ref: StudyLock AI Architecture Specification Section 4.2 & Section 17.1
//

import SwiftUI

struct FocusRoomView: View {
    @StateObject private var screenTime = ScreenTimeManager.shared
    @State private var remainingSeconds: Int = 25 * 60
    @State private var isFocusing: Bool = false
    @State private var isPaused: Bool = false
    @State private var showingEmergencyExitAlert: Bool = false
    
    let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    
    var body: some View {
        ZStack {
            Color(red: 11/255, green: 17/255, blue: 32/255)
                .ignoresSafeArea()
            
            VStack(spacing: 28) {
                // Header Status Pill
                HStack {
                    Label("StudyLock AI", systemImage: "shield.fill")
                        .font(.headline)
                        .foregroundColor(.blue)
                    
                    Spacer()
                    
                    Text(isFocusing ? (isPaused ? "PAUSED" : "ACTIVE") : "READY")
                        .font(.caption)
                        .fontWeight(.bold)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(isFocusing ? Color.green.opacity(0.2) : Color.gray.opacity(0.2))
                        .foregroundColor(isFocusing ? .green : .gray)
                        .cornerRadius(12)
                }
                .padding(.horizontal)
                
                Spacer()
                
                // Dominant Circular Focus Timer
                VStack(spacing: 12) {
                    Text(formatTime(seconds: remainingSeconds))
                        .font(.system(size: 64, weight: .bold, design: .monospaced))
                        .foregroundColor(.white)
                    
                    Text("Deep Focus • Discrete Math Review")
                        .font(.subheadline)
                        .foregroundColor(.gray)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 40)
                .background(Color(red: 17/255, green: 24/255, blue: 39/255))
                .cornerRadius(24)
                .overlay(
                    RoundedRectangle(cornerRadius: 24)
                        .stroke(Color.gray.opacity(0.2), lineWidth: 1)
                )
                .padding(.horizontal)
                
                Spacer()
                
                // Action Controls
                VStack(spacing: 14) {
                    if !isFocusing {
                        Button(action: startFocus) {
                            Text("Start Focus Session")
                                .fontWeight(.semibold)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                        }
                    } else {
                        Button(action: togglePause) {
                            Text(isPaused ? "Resume Session" : "Pause Session")
                                .fontWeight(.semibold)
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(isPaused ? Color.blue : Color.orange)
                                .foregroundColor(.white)
                                .cornerRadius(12)
                        }
                        
                        Button(action: { showingEmergencyExitAlert = true }) {
                            Text("Emergency Exit")
                                .font(.footnote)
                                .foregroundColor(.red)
                        }
                    }
                }
                .padding(.horizontal)
            }
            .padding(.vertical)
        }
        .alert("Emergency Exit", isPresented: $showingEmergencyExitAlert) {
            Button("Exit Session", role: .destructive, action: stopFocus)
            Button("Stay in Focus", role: .cancel) { }
        } message: {
            Text("Emergency exit will restore access to all apps immediately. Session progress will be neutrally recorded.")
        }
        .onReceive(timer) { _ in
            if isFocusing && !isPaused && remainingSeconds > 0 {
                remainingSeconds -= 1
            }
        }
    }
    
    private func startFocus() {
        isFocusing = true
        isPaused = false
        screenTime.applyShields()
    }
    
    private func togglePause() {
        isPaused.toggle()
        if isPaused {
            screenTime.clearShields()
        } else {
            screenTime.applyShields()
        }
    }
    
    private func stopFocus() {
        isFocusing = false
        isPaused = false
        remainingSeconds = 25 * 60
        screenTime.clearShields()
    }
    
    private func formatTime(seconds: Int) -> String {
        let mins = seconds / 60
        let secs = seconds % 60
        return String(format: "%02d:%02d", mins, secs)
    }
}
