---
id: "go-db-gorm-patterns"
title: "Go GORM ORM Patterns"
language: "go"
category: "db"
subcategory: "orm"
tags: ["go", "gorm", "orm", "model", "migration", "query", "transaction"]
version: "1.21+"
retrieval_hint: "Go GORM ORM model migration query transaction hooks preload"
last_verified: "2026-05-24"
confidence: "high"
---

# Go GORM ORM Patterns

## When to Use
- Go projects preferring ORM over raw SQL
- Rapid development with auto-migrations
- Complex queries with relations (joins, preloading)
- Model hooks and callbacks (before/after create, update, delete)

## Standard Pattern

```go
package main

import (
    "gorm.io/driver/postgres"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

// --- Model ---
type User struct {
    ID        uint           `gorm:"primaryKey" json:"id"`
    Name      string         `gorm:"size:100;not null" json:"name"`
    Email     string         `gorm:"size:255;uniqueIndex;not null" json:"email"`
    Age       int            `gorm:"default:0" json:"age"`
    Posts     []Post         `gorm:"foreignKey:UserID" json:"posts,omitempty"`
    CreatedAt time.Time      `json:"created_at"`
    UpdatedAt time.Time      `json:"updated_at"`
    DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
}

type Post struct {
    ID        uint   `gorm:"primaryKey"`
    Title     string `gorm:"size:200;not null"`
    Content   string
    UserID    uint
    CreatedAt time.Time
}

// --- Setup ---
func initDB(dsn string) (*gorm.DB, error) {
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
        Logger: logger.Default.LogMode(logger.Info),
    })
    if err != nil {
        return nil, err
    }

    sqlDB, _ := db.DB()
    sqlDB.SetMaxOpenConns(25)
    sqlDB.SetMaxIdleConns(10)

    return db, nil
}

// --- CRUD ---
type UserRepo struct {
    db *gorm.DB
}

func (r *UserRepo) Create(user *User) error {
    return r.db.Create(user).Error
}

func (r *UserRepo) GetByID(id uint) (*User, error) {
    var user User
    err := r.db.First(&user, id).Error
    if err == gorm.ErrRecordNotFound {
        return nil, nil
    }
    return &user, err
}

func (r *UserRepo) GetWithPosts(id uint) (*User, error) {
    var user User
    err := r.db.Preload("Posts").First(&user, id).Error
    return &user, err
}

func (r *UserRepo) List(page, limit int) ([]User, int64, error) {
    var users []User
    var total int64

    r.db.Model(&User{}).Count(&total)
    err := r.db.Offset((page - 1) * limit).Limit(limit).Find(&users).Error
    return users, total, err
}

func (r *UserRepo) Update(user *User) error {
    return r.db.Save(user).Error
}

func (r *UserRepo) Delete(id uint) error {
    return r.db.Delete(&User{}, id).Error
}

// --- Transactions ---
func (r *UserRepo) Transfer(fromID, toID uint, amount float64) error {
    return r.db.Transaction(func(tx *gorm.DB) error {
        var from, to Account
        if err := tx.First(&from, fromID).Error; err != nil {
            return err
        }
        if err := tx.First(&to, toID).Error; err != nil {
            return err
        }

        from.Balance -= amount
        to.Balance += amount

        if err := tx.Save(&from).Error; err != nil {
            return err
        }
        return tx.Save(&to).Error
    })
}

// --- Hooks ---
func (u *User) BeforeCreate(tx *gorm.DB) error {
    u.Email = strings.ToLower(u.Email)
    return nil
}

// --- Complex queries ---
func (r *UserRepo) Search(query string) ([]User, error) {
    var users []User
    err := r.db.
        Where("name ILIKE ? OR email ILIKE ?", "%"+query+"%", "%"+query+"%").
        Order("created_at DESC").
        Limit(50).
        Find(&users).Error
    return users, err
}

// --- Auto migration ---
func AutoMigrate(db *gorm.DB) error {
    return db.AutoMigrate(&User{}, &Post{})
}
```

## Common Mistakes

```go
// WRONG: Not checking errors
db.Create(&user)  // Error silently ignored

// CORRECT: Always check errors
if err := db.Create(&user).Error; err != nil {
    return err
}

// WRONG: Using Find without Limit
db.Find(&users)  // Loads entire table!

// CORRECT: Always Limit with Find
db.Limit(100).Find(&users)

// WRONG: Not using Preload (N+1 query)
users, _ := repo.List(1, 20)
for _, user := range users {
    db.Model(&user).Association("Posts").Find(&user.Posts)  // N queries!
}

// CORRECT: Preload relations
db.Preload("Posts").Find(&users)  // 2 queries total

// WRONG: Soft delete not working (missing DeletedAt)
type User struct {
    ID   uint
    Name string
    // No DeletedAt field!
}
db.Delete(&user)  // Permanently deletes

// CORRECT: Add DeletedAt for soft deletes
type User struct {
    ID        uint
    Name      string
    DeletedAt gorm.DeletedAt `gorm:"index"`
}
```

## Gotchas
- `db.First(&user, id)` returns `ErrRecordNotFound` if not found
- `db.Save()` updates all fields; `db.Updates()` updates only non-zero fields
- `Preload("Posts")` loads relations in separate queries; `Joins("Posts")` uses JOIN
- Soft deletes: `DeletedAt` field must be present; `db.Unscoped()` ignores soft deletes
- `db.Transaction()` auto-rolls back on error, auto-commits on success
- `AutoMigrate` creates/alters tables but doesn't drop columns
- Hooks (`BeforeCreate`, `AfterUpdate`) run within the transaction
- Use `db.Session(&gorm.Session{})` for per-session configuration

## Related
- go/db/database-sql.md
- go/testing/testing.md
- go/stdlib/error-handling.md
