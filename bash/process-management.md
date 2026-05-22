---
id: "bash-process-management"
title: "Process Management in Shell Scripts"
language: "bash"
category: "stdlib"
tags: ["bash", "shell", "process", "background", "jobs", "signals"]
version: "n/a"
retrieval_hint: "bash background process jobs wait kill signal nohup"
last_verified: "2026-05-22"
confidence: "high"
---

# Process Management in Shell Scripts

## When to Use
- Running commands in the background
- Managing multiple concurrent processes
- Handling signals for graceful shutdown
- Parallel execution of tasks

## Standard Pattern

```bash
#!/usr/bin/env bash
set -euo pipefail

# Run command in background
long_running_task &
bg_pid=$!
echo "Background PID: $bg_pid"

# Wait for specific background process
wait "$bg_pid"
echo "Exit code: $?"

# Wait for all background processes
wait

# Parallel execution with wait
task1 &
pid1=$!
task2 &
pid2=$!
task3 &
pid3=$!

# Wait for all and check results
failed=0
for pid in $pid1 $pid2 $pid3; do
    if ! wait "$pid"; then
        echo "PID $pid failed"
        failed=$((failed + 1))
    fi
done
[[ $failed -eq 0 ]] || exit 1

# Background jobs with job control
jobs -l           # List background jobs
fg %1             # Bring job 1 to foreground
bg %1             # Resume job 1 in background
disown %1         # Detach job from shell (won't be killed on logout)

# nohup: survive logout
nohup ./long_task.sh > output.log 2>&1 &
disown

# Signals and signal handling
# Common signals: SIGHUP(1), SIGINT(2), SIGTERM(15), SIGKILL(9)
trap 'echo "Received SIGHUP"' HUP
trap 'echo "Received SIGINT"; cleanup; exit 130' INT
trap 'echo "Received SIGTERM"; cleanup; exit 143' TERM

cleanup() {
    echo "Cleaning up..."
    # Kill child processes
    kill "$pid1" "$pid2" 2>/dev/null || true
    wait "$pid1" "$pid2" 2>/dev/null || true
}
trap cleanup EXIT

# Parallel execution with xargs
find . -name "*.txt" -print0 | xargs -0 -P 4 -I {} process_file {}
# -P 4: run 4 processes in parallel
# -I {}: placeholder for each argument

# GNU parallel (if available)
find . -name "*.txt" | parallel -j4 process_file {}

# Timeout for commands
timeout 10s long_running_command
exit_code=$?
if [[ $exit_code -eq 124 ]]; then
    echo "Command timed out"
fi

# Process substitution with background
diff <(sort file1.txt) <(sort file2.txt)

# PID file management
PIDFILE="/var/run/myapp.pid"
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT
```

## Common Mistakes

```bash
# WRONG: Not waiting for background processes (zombie processes)
./task1.sh &
./task2.sh &
exit 0  # Child processes may be killed

# CORRECT: Wait for all children
./task1.sh &
./task2.sh &
wait

# WRONG: Ignoring background process failures
./task1.sh &
./task2.sh &
wait
# Doesn't check if tasks succeeded

# CORRECT: Check exit codes
failed=0
./task1.sh & pid1=$!
./task2.sh & pid2=$!
wait "$pid1" || failed=$((failed + 1))
wait "$pid2" || failed=$((failed + 1))
[[ $failed -eq 0 ]] || exit 1

# WRONG: Killing without checking if process exists
kill "$pid" 2>/dev/null  # Suppresses error but doesn't handle it

# CORRECT: Check if process is running first
if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    wait "$pid" || true
fi

# WRONG: Using SIGKILL as first resort
kill -9 "$pid"  # Can't be trapped, no cleanup

# CORRECT: Try SIGTERM first, then SIGKILL
kill "$pid" 2>/dev/null || true
sleep 2
kill -0 "$pid" 2>/dev/null && kill -9 "$pid" || true

# WRONG: Race condition in PID file
echo $$ > "$PIDFILE"  # Another process may have written between check and write

# CORRECT: Use file locking
exec 200>"$PIDFILE"
flock -n 200 || { echo "Already running"; exit 1; }
echo $$ >&200
```

## Gotchas
- `&` puts a command in the background — `$!` holds its PID
- `wait` without arguments waits for ALL background jobs
- `wait $pid` returns the exit code of that process
- `disown` detaches a job from the shell — it won't receive SIGHUP on logout
- `nohup` ignores SIGHUP — use for tasks that should survive logout
- `trap` handlers are executed in the main shell, not in subshells
- `kill -0 $pid` checks if a process exists without sending a signal
- `timeout` returns exit code 124 if the command times out
- `xargs -P` is a simple way to run commands in parallel
- Background processes inherit file descriptors — close unused ones to avoid hangs
- `wait` on a PID that doesn't exist returns 127
- Signal handlers run between commands, not during command execution

## Related
- bash/error-handling.md
- bash/scripting-patterns.md
- python/stdlib/subprocess.md
