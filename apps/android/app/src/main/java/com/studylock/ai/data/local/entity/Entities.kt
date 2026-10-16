package com.studylock.ai.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.util.UUID

@Entity(tableName = "local_tasks")
data class TaskEntity(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val title: String,
    val description: String?,
    val subject: String?,
    val priority: Int = 2,
    val estimatedMinutes: Int = 30,
    val dueAtEpochMs: Long?,
    val status: String = "todo",
    val revision: Int = 1,
    val deletedAtEpochMs: Long? = null,
    val isPendingSync: Boolean = true
)

@Entity(tableName = "local_sessions")
data class FocusSessionEntity(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val taskId: String?,
    val plannedMinutes: Int = 25,
    val actualSeconds: Int = 0,
    val pausedSeconds: Int = 0,
    val startedAtEpochMs: Long,
    val endedAtEpochMs: Long? = null,
    val state: String = "FOCUSING",
    val enforcementState: String = "ACTIVE",
    val interruptions: Int = 0,
    val isPendingSync: Boolean = true
)

@Entity(tableName = "local_block_rules")
data class BlockRuleEntity(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val targetType: String, // app_package, domain, url_pattern
    val targetValue: String,
    val action: String = "block",
    val isEnabled: Boolean = true,
    val revision: Int = 1,
    val isPendingSync: Boolean = false
)
