---
id: "kotlin-db-room"
title: "Room Database: Entities, DAOs, Migrations, Relationships"
language: "kotlin"
category: "db"
tags: ["kotlin", "android", "room", "database", "dao", "migrations", "orm"]
version: "2.6+"
retrieval_hint: "kotlin room database entity DAO migration relationship TypeConverter"
last_verified: "2026-05-24"
confidence: "high"
---

# Room Database: Entities, DAOs, Migrations, Relationships

## When to Use
- Storing structured data locally in Android apps
- Using SQLite with compile-time query verification
- Defining relationships between data entities
- Managing database schema migrations

## Standard Pattern

```kotlin
import androidx.room.*
import kotlinx.coroutines.flow.Flow

// --- Entity ---
@Entity(
    tableName = "users",
    indices = [
        Index(value = ["email"], unique = true),
        Index(value = ["created_at"])
    ]
)
data class User(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "name")
    val name: String,

    @ColumnInfo(name = "email")
    val email: String,

    @ColumnInfo(name = "age")
    val age: Int? = null,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis()
)

// --- Related Entity ---
@Entity(
    tableName = "posts",
    foreignKeys = [
        ForeignKey(
            entity = User::class,
            parentColumns = ["id"],
            childColumns = ["user_id"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["user_id"])]
)
data class Post(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "title")
    val title: String,

    @ColumnInfo(name = "content")
    val content: String,

    @ColumnInfo(name = "user_id")
    val userId: Long
)

// --- TypeConverter ---
class Converters {
    @TypeConverter
    fun fromTimestamp(value: Long?): Date? {
        return value?.let { Date(it) }
    }

    @TypeConverter
    fun dateToTimestamp(date: Date?): Long? {
        return date?.time
    }

    // Convert list to JSON string
    @TypeConverter
    fun fromStringList(value: String): List<String> {
        return value.split(",").filter { it.isNotEmpty() }
    }

    @TypeConverter
    fun toStringList(list: List<String>): String {
        return list.joinToString(",")
    }
}

// --- Data Access Object (DAO) ---
@Dao
interface UserDao {
    @Query("SELECT * FROM users ORDER BY name ASC")
    fun getAllUsers(): Flow<List<User>>

    @Query("SELECT * FROM users WHERE id = :id")
    suspend fun getUserById(id: Long): User?

    @Query("SELECT * FROM users WHERE email = :email")
    suspend fun getUserByEmail(email: String): User?

    @Query("SELECT * FROM users WHERE age >= :minAge")
    fun getUsersOlderThan(minAge: Int): Flow<List<User>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertUser(user: User): Long

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertUsers(users: List<User>): List<Long>

    @Update
    suspend fun updateUser(user: User): Int

    @Delete
    suspend fun deleteUser(user: User): Int

    @Query("DELETE FROM users WHERE id = :id")
    suspend fun deleteUserById(id: Long): Int

    // Transaction — multiple operations as one unit
    @Transaction
    suspend fun insertUserWithPosts(user: User, posts: List<Post>) {
        val userId = insertUser(user)
        posts.forEach { it.userId = userId }
        // Insert posts...
    }
}

// --- Relationship Query ---
data class UserWithPosts(
    @Embedded val user: User,
    @Relation(
        parentColumn = "id",
        entityColumn = "user_id"
    )
    val posts: List<Post>
)

@Dao
interface PostDao {
    @Transaction
    @Query("SELECT * FROM users")
    fun getUsersWithPosts(): Flow<List<UserWithPosts>>
}

// --- Database Class ---
@Database(
    entities = [User::class, Post::class],
    version = 2,
    exportSchema = true
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun postDao(): PostDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "app_database"
                )
                    .addMigrations(MIGRATION_1_2)
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

// --- Migration ---
val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(database: SupportSQLiteDatabase) {
        database.execSQL("ALTER TABLE users ADD COLUMN age INTEGER DEFAULT NULL")
        database.execSQL("CREATE TABLE IF NOT EXISTS `posts` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, `title` TEXT NOT NULL, `content` TEXT NOT NULL, `user_id` INTEGER NOT NULL, FOREIGN KEY(`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE)")
    }
}
```

## Common Mistakes

```kotlin
// WRONG: Forgetting @Entity annotation
data class User(  // No @Entity!
    @PrimaryKey val id: Int,
    val name: String
)
// Room won't process this class

// CORRECT: Add @Entity
@Entity(tableName = "users")
data class User( ... )


// WRONG: Schema migration without testing
// Running app with new entity fields crashes
// java.lang.IllegalStateException: Room cannot verify the data integrity

// CORRECT: Write migrations or use fallbackToDestructiveMigration()
Room.databaseBuilder(...)
    .addMigrations(MIGRATION_1_2)
    .build()
// Or for development: .fallbackToDestructiveMigration()


// WRONG: Not using suspend for DAO methods that run on background
@Dao
interface UserDao {
    @Query("SELECT * FROM users")
    fun getAllUsers(): List<User>  // Blocks main thread!
}

// CORRECT: Return Flow (observable) or use suspend
@Dao
interface UserDao {
    @Query("SELECT * FROM users")
    fun getAllUsers(): Flow<List<User>>  // Auto-dispatched
}


// WRONG: Foreign key without index
// Querying by user_id on posts table will be slow without index

// CORRECT: Add index on foreign key columns
@Entity(
    foreignKeys = [ForeignKey(entity = User::class, ...)],
    indices = [Index(value = ["user_id"])]
)
```

## Gotchas
- **Migration fallback to destructive**: `fallbackToDestructiveMigration()` deletes all data on migration mismatch. Never use in production. Always write proper migrations for production apps.
- **Foreign key index requirement**: Room requires explicit indices on foreign key columns. Without them, Room logs a warning and queries perform poorly.
- **Flow on DAO methods**: Room automatically dispatches `Flow` queries on a background thread. You don't need `flowOn(Dispatchers.IO)` for Room Flow queries.
- **TypeConverters scope**: `@TypeConverters` on the Database class applies to all entities and DAOs. On individual entities, it applies only to that entity. On DAO methods, it applies only to that method.
- **Auto-migration (Room 2.4+)**: Room supports auto-migrations via `@Database(autoMigrations = [AutoMigration(from = 1, to = 2)])`. Works only for simple changes (column add, not renames).
- **Thread safety**: Room DAO methods are thread-safe by default. Queries with `suspend` use `Dispatchers.IO`. `Flow` queries observe changes automatically.
- **Export schema**: `exportSchema = true` generates a JSON schema file in the `schemas/` directory. Commit this to version control for migration testing.

## Related
- kotlin/stdlib/coroutines.md
- kotlin/db/exposed.md
- kotlin/testing/mocking.md
