package com.studylock.ai.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// Calm Navy Theme Colors (Spec Section 17.1)
val NavyBackground = Color(0xFF0B1120)
val CardSurface = Color(0xFF111827)
val AccentBlue = Color(0xFF3B82F6)
val TextPrimary = Color(0xFFF9FAFB)
val TextMuted = Color(0xFF9CA3AF)
val StatusGreen = Color(0xFF10B981)

@Composable
fun FocusRoomScreen(
    currentTaskTitle: String = "Distributed Systems Exam Prep",
    plannedMinutes: Int = 25,
    onPause: () -> Unit = {},
    onResume: () -> Unit = {},
    onFinish: () -> Unit = {},
    onEmergencyExit: () -> Unit = {}
) {
    var isPaused by remember { mutableStateOf(false) }
    var showExitDialog by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(NavyBackground)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.SpaceBetween
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "🛡️ StudyLock AI",
                color = AccentBlue,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Surface(
                color = if (!isPaused) StatusGreen.copy(alpha = 0.2f) else Color(0xFFF59E0B).copy(alpha = 0.2f),
                shape = RoundedCornerShape(16.dp)
            ) {
                Text(
                    text = if (!isPaused) "ACTIVE ENFORCEMENT" else "PAUSED",
                    color = if (!isPaused) StatusGreen else Color(0xFFF59E0B),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                )
            }
        }

        // Center Timer Display
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 32.dp),
            colors = CardDefaults.cardColors(containerColor = CardSurface),
            shape = RoundedCornerShape(20.dp)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = currentTaskTitle,
                    color = TextMuted,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "24:45",
                    color = TextPrimary,
                    fontSize = 56.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "$plannedMinutes Minute Planned Block",
                    color = TextMuted,
                    fontSize = 13.sp
                )
            }
        }

        // Controls
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Button(
                onClick = {
                    isPaused = !isPaused
                    if (isPaused) onPause() else onResume()
                },
                modifier = Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.buttonColors(containerColor = AccentBlue),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = if (isPaused) "Resume Session" else "Pause Session",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            OutlinedButton(
                onClick = onFinish,
                modifier = Modifier.fillMaxWidth().height(52.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = TextPrimary),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Complete Early", fontSize = 16.sp)
            }

            TextButton(
                onClick = { showExitDialog = true },
                modifier = Modifier.align(Alignment.CenterHorizontally)
            ) {
                Text(
                    text = "Emergency Exit",
                    color = Color(0xFFEF4444),
                    fontSize = 14.sp
                )
            }
        }
    }

    if (showExitDialog) {
        AlertDialog(
            onDismissRequest = { showExitDialog = false },
            title = { Text("Emergency Exit") },
            text = { Text("Are you sure you want to exit? Your focus duration so far will be saved, but completion rewards require finishing the planned duration.") },
            confirmButton = {
                TextButton(onClick = {
                    showExitDialog = false
                    onEmergencyExit()
                }) {
                    Text("Exit Session", color = Color(0xFFEF4444))
                }
            },
            dismissButton = {
                TextButton(onClick = { showExitDialog = false }) {
                    Text("Stay in Focus")
                }
            }
        )
    }
}
