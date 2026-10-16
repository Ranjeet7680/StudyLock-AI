package com.studylock.ai.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.studylock.ai.adapter.AndroidBlockingAdapter

class FocusSessionService : Service() {

    private val CHANNEL_ID = "studylock_focus_channel"
    private val NOTIFICATION_ID = 1001
    private lateinit var blockingAdapter: AndroidBlockingAdapter

    override fun onCreate() {
        super.onCreate()
        blockingAdapter = AndroidBlockingAdapter(applicationContext)
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action ?: "START"
        val plannedMinutes = intent?.getIntExtra("PLANNED_MINUTES", 25) ?: 25
        val sessionId = intent?.getStringExtra("SESSION_ID") ?: ""

        when (action) {
            "START" -> {
                val notification = buildNotification("Deep Focus Active", "Stay focused. Distractions are restricted.")
                startForeground(NOTIFICATION_ID, notification)
                blockingAdapter.applyFocusRestrictions()
            }
            "PAUSE" -> {
                val notification = buildNotification("Focus Session Paused", "Restrictions temporarily paused.")
                val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                manager.notify(NOTIFICATION_ID, notification)
                blockingAdapter.pauseRestrictions()
            }
            "STOP" -> {
                blockingAdapter.clearRestrictions()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
            }
        }

        return START_STICKY // Ensures service restart if killed by OS (Section 7.2 & 15.2)
    }

    private fun buildNotification(title: String, content: String): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(title)
            .setContentText(content)
            .setSmallIcon(android.R.drawable.ic_lock_idle_lock)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "StudyLock Focus Session",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Shows persistent progress during active study focus sessions"
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
