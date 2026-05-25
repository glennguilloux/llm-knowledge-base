---
id: "patterns-feature-flags"
title: "Feature Flags Patterns"
language: "multi"
category: "patterns"
subcategory: "operations"
tags: ["feature-flags", "toggle", "rollout", "experiment", "a-b-testing"]
version: ""
retrieval_hint: "Feature flags toggle rollout experiment A/B testing gradual release"
last_verified: "2026-05-24"
confidence: "high"
---

# Feature Flags Patterns

## When to Use
- Gradual feature rollouts (10% → 50% → 100% of users)
- A/B testing different implementations
- Kill switches for problematic features
- Trunk-based development (merge to main, flag-gated release)

## Standard Pattern

```python
# --- Simple feature flag ---
import os

def is_enabled(flag_name: str, default: bool = False) -> bool:
    return os.environ.get(f"FEATURE_{flag_name.upper()}", str(default)).lower() == "true"

if is_enabled("new_dashboard"):
    return new_dashboard_view()
else:
    return legacy_dashboard_view()
```

```typescript
// --- Feature flag with context ---
interface FeatureFlag {
  name: string;
  enabled: boolean;
  rolloutPercentage: number;
  allowedUsers: string[];
}

class FeatureFlags {
  private flags: Map<string, FeatureFlag>;

  isEnabled(flagName: string, user?: User): boolean {
    const flag = this.flags.get(flagName);
    if (!flag) return false;

    if (!flag.enabled) return false;
    if (flag.allowedUsers.includes(user?.id ?? "")) return true;

    // Percentage rollout (deterministic per user)
    if (user && flag.rolloutPercentage < 100) {
      const hash = this.hashUser(user.id, flagName);
      return hash < flag.rolloutPercentage;
    }

    return flag.enabled;
  }

  private hashUser(userId: string, flagName: string): number {
    // Deterministic hash: same user always gets same result
    const hash = [...userId + flagName].reduce((h, c) => {
      return ((h << 5) - h + c.charCodeAt(0)) | 0;
    }, 0);
    return Math.abs(hash) % 100;
  }
}

// --- React component ---
function Dashboard() {
  const flags = useFeatureFlags();

  if (flags.isEnabled("new-dashboard", user)) {
    return <NewDashboard />;
  }
  return <LegacyDashboard />;
}
```

```typescript
// --- LaunchDarkly / GrowthBook integration ---
import { withLDProvider, useLDClient } from "launchdarkly-react-client-sdk";

function Dashboard() {
  const showNewDashboard = useFlags().newDashboard;

  return showNewDashboard ? <NewDashboard /> : <LegacyDashboard />;
}
```

## Common Mistakes

```text
# WRONG: Feature flag checked everywhere (scattered logic)
if is_enabled("new_feature"):
    # ... in 50 different files

# CORRECT: Check once at the boundary
def get_handler(request):
    if is_enabled("new_feature"):
        return new_feature_handler
    return legacy_handler

# WRONG: Dead flags never removed
if is_enabled("old_feature"):  # Always true, been 2 years
    # Dead code behind always-on flag

# CORRECT: Remove flags after full rollout
# Track flag lifecycle: created → partial → full → removed

# WRONG: Using feature flags for permanent configuration
if is_enabled("use_postgres"):  # This is config, not a feature flag
    db = postgres_connect()

# CORRECT: Feature flags are temporary; config is permanent
```

## Gotchas
- Feature flags should be temporary — remove them after full rollout
- Use deterministic hashing for percentage rollouts (same user gets same experience)
- Flags should be controlled remotely (not just env vars) for quick rollback
- Test both paths: flag on AND flag off
- Use kill switches for instant rollback without deployment
- Separate feature flags from experiment flags (different lifecycle)
- Document each flag: owner, purpose, expected removal date
- Consider LaunchDarkly, GrowthBook, or Unleash for production feature flag management

## Related
- patterns/graceful-shutdown.md
- api-design/versioning.md
- patterns/health-checks.md
