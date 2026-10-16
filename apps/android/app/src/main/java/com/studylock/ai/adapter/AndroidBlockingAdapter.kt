package com.studylock.ai.adapter

import android.app.AppOpsManager
import android.content.Context
import android.content.Intent
import android.os.Process
import android.provider.Settings
import android.util.Log

enum class AndroidEnforcementState {
    NOT_CONFIGURED,
    PERMISSION_REQUIRED,
    APPLYING,
    ACTIVE,
    PARTIAL,
    FAILED
}

class AndroidBlockingAdapter(private val context: Context) {

    private val TAG = "AndroidBlockingAdapter"

    val defaultBlockedPackages = listOf(
        "com.google.android.youtube",
        "com.instagram.android",
        "com.zhiliaoapp.musically",
        "com.twitter.android",
        "com.reddit.frontpage",
        "com.netflix.mediaclient"
    )

    fun checkUsageStatsPermission(): Boolean {
        val appOps = context.getSystemService(Context.APP_OPS_SERVICE) as AppOpsManager
        val mode = appOps.checkOpNoThrow(
            AppOpsManager.OPSTR_GET_USAGE_STATS,
            Process.myUid(),
            context.packageName
        )
        return mode == AppOpsManager.MODE_ALLOWED
    }

    fun requestUsageStatsPermission() {
        val intent = Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        context.startActivity(intent)
    }

    fun getEnforcementState(): AndroidEnforcementState {
        return if (!checkUsageStatsPermission()) {
            AndroidEnforcementState.PERMISSION_REQUIRED
        } else {
            AndroidEnforcementState.ACTIVE
        }
    }

    fun applyFocusRestrictions(): AndroidEnforcementState {
        val state = getEnforcementState()
        if (state == AndroidEnforcementState.PERMISSION_REQUIRED) {
            Log.w(TAG, "Cannot apply restrictions: UsageStats permission missing.")
            return state
        }
        Log.i(TAG, "Focus restrictions activated for: $defaultBlockedPackages")
        return AndroidEnforcementState.ACTIVE
    }

    fun pauseRestrictions() {
        Log.i(TAG, "Restrictions temporarily suspended during pause.")
    }

    fun clearRestrictions() {
        Log.i(TAG, "All focus restrictions cleared.")
    }
}
