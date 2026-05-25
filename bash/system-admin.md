---
id: "bash-system-admin"
title: "System Administration: Processes, Logs, Services, Monitoring"
language: "bash"
category: "devops"
tags: ["bash", "system-admin", "processes", "logs", "monitoring", "services"]
version: "n/a"
retrieval_hint: "bash system administration processes logs journalctl systemctl monitoring health checks"
last_verified: "2026-05-24"
confidence: "high"
---

# System Administration: Processes, Logs, Services, Monitoring

## When to Use
- Monitoring and managing system resources
- Debugging production issues (CPU, memory, disk, network)
- Managing services with systemd
- Analyzing log files for patterns and anomalies
- Writing health checks and diagnostic scripts

## Standard Pattern

```bash
# === Process Management ===

# List processes with details
ps aux --sort=-%cpu | head -10               # Top 10 CPU consumers
ps aux --sort=-%mem | head -10               # Top 10 memory consumers
ps -eo pid,ppid,cmd,%cpu,%mem,start,etime     # Custom columns

# Process tree
ps --forest -u www-data

# lsof — what files/sockets a process has open
lsof -p 1234                                 # Files opened by PID 1234
lsof -i :8080                                # What's listening on port 8080
lsof -u ubuntu                               # Files opened by user ubuntu

# Find and kill processes
pgrep -f "myapp"                             # PID by pattern
pkill -f "myapp"                             # Kill by pattern
kill -15 1234                                # Graceful SIGTERM
kill -9 5678                                 # Force kill SIGKILL (last resort)

# --- Memory ---

# Memory stats
free -h                                      # Human-readable
cat /proc/meminfo | grep -E "^(MemTotal|MemAvailable|SwapTotal)"

# Top memory consumers
ps aux --sort=-%mem | awk 'NR<=10 {printf "%-6s %-6s %s\n", $2, $4"%", $11}'

# --- Disk ---

# Disk usage
df -h                                        # Filesystem usage
du -sh /var/log/*                            # Directory sizes
du -h --max-depth=1 /var/ | sort -hr         # Sorted sizes

# Find large files
find /var -type f -size +100M -exec ls -lh {} \; 2>/dev/null

# Inode usage
df -i                                        # Check for inode exhaustion

# I/O stats
iostat -xz 1                                 # Disk I/O (1s intervals)
iotop                                        # Per-process I/O (requires root)

# --- Network ---

# Listening services
ss -tlnp                                     # TCP listening sockets (modern)
netstat -tlnp                                # TCP listening sockets (legacy)

# Connection stats
ss -tun | grep -v "State" | awk '{print $1}' | sort | uniq -c
# TCP connections by state
ss -t state established | wc -l

# Bandwidth monitoring
iftop -i eth0                                # Per-connection bandwidth
nethogs eth0                                 # Per-process bandwidth

# DNS resolution
dig +short example.com                       # A record
nslookup example.com 8.8.8.8                # Query specific DNS server
host -t MX example.com                       # MX records

# --- Logs ---

# systemd journal
journalctl -u myapp.service                  # Service logs
journalctl -u myapp.service --since "1 hour ago"
journalctl -u myapp.service -f               # Follow (like tail -f)
journalctl -u myapp.service -o json-pretty   # JSON format

# Traditional logs
tail -f /var/log/nginx/access.log            # Follow live
tail -n 500 /var/log/syslog | grep -i error  # Recent errors
less +F /var/log/myapp.log                   # Follow in less (Shift+F)

# --- Health Check Pattern ---

check_service() {
    local service="$1"
    if systemctl is-active --quiet "$service"; then
        echo "OK: $service is running"
    else
        echo "CRITICAL: $service is NOT running" >&2
        systemctl restart "$service" && echo "Restarted $service"
    fi
}

check_disk() {
    local threshold="${1:-90}"  # Default 90%
    df -h | awk -v t="$threshold" 'NR>1 {
        gsub(/%/,"",$5);
        if ($5+0 > t+0) {
            printf "WARNING: %s at %s%% (%s)\n", $6, $5, $1
        }
    }'
}

# --- Diagnostic Collection Script ---

collect_diagnostics() {
    local output_dir="/tmp/diag-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$output_dir"

    {
        echo "=== CPU ==="
        top -bn1 | head -5
        echo "=== Memory ==="
        free -h
        echo "=== Disk ==="
        df -h
        echo "=== Network ==="
        ss -tlnp
        echo "=== Processes ==="
        ps aux --sort=-%cpu | head -20
        echo "=== Load ==="
        uptime
    } > "$output_dir/system.txt"

    tar czf "${output_dir}.tar.gz" -C /tmp "diag-$(date +%Y%m%d-%H%M%S)"
    echo "Diagnostics saved to ${output_dir}.tar.gz"
}

# --- Cron Pattern ---

# Run every 5 minutes
# */5 * * * * /usr/local/bin/health_check.sh

# Rotate logs
# 0 0 * * * find /var/log/myapp -mtime +30 -delete
```

## Common Mistakes

```bash
# WRONG: Using kill -9 as first resort (no cleanup, data corruption)
kill -9 1234  # SIGKILL — process has no chance to clean up

# CORRECT: Try graceful shutdown first
kill -15 1234  # SIGTERM — process can handle cleanup
# Wait, then escalate
sleep 5
kill -9 1234  # Only if still alive after timeout


# WRONG: Parsing ls output (fragile, breaks on special chars)
for file in $(ls /var/log/); do echo "$file"; done

# CORRECT: Use glob or find
for file in /var/log/*; do echo "$(basename "$file")"; done


# WRONG: Not handling missing tools gracefully
if ! command -v jq &>/dev/null; then
    echo "jq is required but not installed"
    exit 1
fi


# WRONG: Using netstat (deprecated, not installed by default on modern systems)
netstat -tlnp

# CORRECT: Use ss instead
ss -tlnp


# WRONG: Checking exit code with $? unnecessarily
grep -q "error" /var/log/syslog
if [ $? -eq 0 ]; then
    echo "Found errors"
fi

# CORRECT: Use the command directly in condition
if grep -q "error" /var/log/syslog; then
    echo "Found errors"
fi
```

## Gotchas
- **OOM killer**: When memory is exhausted, the kernel's OOM killer selects processes to kill. Check `dmesg | grep -i oom` to see if your process was killed. Set `vm.overcommit_memory=2` to prevent overcommit.
- **fd exhaustion**: Every open file uses a file descriptor. Default ulimit is often 1024. Server processes may hit `Too many open files`. Check with `lsof -p PID | wc -l` and raise with `ulimit -n 65536`.
- **Zombie processes**: A zombie (defunct) process is a child that exited but wasn't waited on. If init reaps them, you can't kill them. Fix the parent process to properly `wait()` on children.
- **Filesystem full vs inode full**: `df -h` shows space, `df -i` shows inodes. It's possible to have free space but no free inodes (too many tiny files), causing "disk full" errors.
- **timedatectl and logs**: System logs use the system clock. If your timezone or clock is wrong, log timestamps will be misleading. Always set `timedatectl set-timezone UTC` on servers.
- **Shell vs systemd environment**: Systemd services have a minimal environment by default. `PATH` is limited, and many environment variables ($HOME, etc.) are not set unless explicitly configured. Always use absolute paths in service files.

## Related
- bash/process-management.md
- bash/testing-debugging.md
- bash/error-handling.md
