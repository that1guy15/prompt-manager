# 🧹 Log Sanitization Documentation

## Overview

The Log Sanitization feature intelligently filters repetitive patterns from logs, making them more concise and token-efficient for AI prompts. It's designed to handle verbose application logs, server logs, and any text with repetitive patterns.

## Key Features

✅ **Intelligent Pattern Detection** - Fuzzy matching identifies similar but not identical lines  
✅ **Automatic Summarization** - Replaces repetitive blocks with concise summaries  
✅ **Sensitive Data Detection** - Warns about potential API keys, passwords, and tokens  
✅ **Flexible I/O** - Works with clipboard, files, or piped input  
✅ **Configurable Thresholds** - Fine-tune pattern matching sensitivity  
✅ **Statistics Reporting** - Shows reduction metrics and pattern analysis  

## Quick Start

### Basic Usage (Clipboard)

```bash
# Sanitize clipboard content (most common use case)
./pmcli sanitize

# Preview without modifying clipboard
./pmcli sanitize -p

# Show statistics about the sanitization
./pmcli sanitize -s
```

### File Operations

```bash
# Sanitize a log file
./pmcli sanitize -i server.log -o server_clean.log

# Sanitize from file to clipboard
./pmcli sanitize -i debug.log

# Preview file sanitization
./pmcli sanitize -i app.log -p
```

### Advanced Options

```bash
# Adjust similarity threshold (lower = more aggressive filtering)
./pmcli sanitize -t 0.7

# Change minimum repetitions before filtering
./pmcli sanitize -m 5

# Disable sensitive data warnings
./pmcli sanitize --no-sensitive-check

# Combine options
./pmcli sanitize -i logs.txt -t 0.8 -m 4 -s
```

## How It Works

### Pattern Detection Algorithm

1. **Line Normalization**: Timestamps, IPs, UUIDs, and numbers are normalized for comparison
2. **Similarity Calculation**: Uses sequence matching to find similar lines (default: 85% similarity)
3. **Pattern Grouping**: Groups similar lines that appear multiple times
4. **Smart Summarization**: Replaces groups with context-aware summaries

### Example Transformation

**Before** (200+ lines):
```
artist-dashboard-worker | DEBUG: Session created: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker | DEBUG: get_async_session called, returning type: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker | DEBUG: Session created: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker | DEBUG: get_async_session called, returning type: <class 'sqlalchemy.orm.session.AsyncSession'>
[... 50 more similar lines ...]
artist-dashboard-worker | 2025-07-28 20:50:54,961 - app.upload_system.scheduler - DEBUG - Checking for due scheduled uploads
artist-dashboard-worker | 2025-07-28 20:50:54,961 - app.upload_system.worker - DEBUG - Processing scheduled tasks
[... 20 more similar lines ...]
```

**After** (10 lines):
```
artist-dashboard-worker | DEBUG: Session created: <class 'sqlalchemy.orm.session.AsyncSession'>
artist-dashboard-worker | DEBUG: get_async_session called, returning type: <class 'sqlalchemy.orm.session.AsyncSession'>
[... 50 similar session creation messages filtered ...]
artist-dashboard-worker | 2025-07-28 20:50:54,961 - app.upload_system.scheduler - DEBUG - Checking for due scheduled uploads
artist-dashboard-worker | 2025-07-28 20:50:54,961 - app.upload_system.worker - DEBUG - Processing scheduled tasks
[... 20 task processing messages filtered ...]
```

## Pattern Recognition

### Automatically Detected Patterns

- **Session Creation**: Database/ORM session initialization
- **Health Checks**: HTTP health endpoint requests
- **Task Processing**: Scheduler and worker status messages
- **No-op Messages**: "No tasks", "Nothing to process", etc.
- **Connection Logs**: Connect/disconnect events
- **Debug Traces**: Stack traces and debug output

### Normalization Rules

| Pattern | Normalized To | Example |
|---------|---------------|---------|
| Timestamps | `<TIMESTAMP>` | `2025-07-28 20:50:54` → `<TIMESTAMP>` |
| IP Addresses | `<IP>` | `127.0.0.1:8080` → `<IP>` |
| UUIDs | `<UUID>` | `a1b2c3d4-e5f6-...` → `<UUID>` |
| Hex Addresses | `<HEX>` | `0x7f8b4c` → `<HEX>` |
| Port Numbers | `<PORT>` | `:8080` → `:<PORT>` |
| File:Line | `file:<LINE>` | `app.py:123` → `app.py:<LINE>` |

## Security Features

### Sensitive Data Detection

The sanitizer scans for common patterns that might indicate sensitive data:

- **API Keys**: `api_key=...`, `apiKey: ...`
- **Tokens**: `token=...`, `Bearer ...`
- **Passwords**: `password=...`, `pwd: ...`
- **Secrets**: `secret=...`, `private_key=...`
- **AWS Credentials**: `aws_access_key_id`, `aws_secret_access_key`

When detected, you'll see:
```
⚠️  Sensitive data detected:
   - Potential API Key detected
   - Potential Bearer Token detected

Proceed with sanitization? (y/N):
```

### Safe Handling

- Sensitive data detection runs **before** any processing
- Original content is never logged or stored
- Sanitized output can still contain masked sensitive data
- Use `--no-sensitive-check` at your own risk

## Configuration

### Tuning Parameters

**Similarity Threshold** (`-t, --threshold`)
- Range: 0.0 to 1.0 (default: 0.85)
- Lower values = more aggressive filtering
- Higher values = only exact matches filtered
- Recommended: 0.7-0.9 depending on log verbosity

**Minimum Repetitions** (`-m, --min-reps`)
- Default: 3 occurrences before filtering
- Increase for more conservative filtering
- Decrease for aggressive compression

### Environment Variables

```bash
# Default similarity threshold
export PM_SANITIZE_THRESHOLD=0.85

# Default minimum repetitions
export PM_SANITIZE_MIN_REPS=3

# Disable sensitive data check by default
export PM_SANITIZE_NO_SENSITIVE_CHECK=1
```

### Config File (~/.pm_sanitize.json)

```json
{
  "similarity_threshold": 0.85,
  "min_repetitions": 3,
  "context_lines": 2,
  "preserve_timestamps": false,
  "max_example_lines": 2,
  "sensitive_data_check": true,
  "patterns": {
    "custom_pattern": "regex_here"
  }
}
```

## Use Cases

### 1. Docker Compose Logs
```bash
# Clean up verbose docker-compose logs
docker-compose logs | ./pmcli sanitize -o cleaned_logs.txt
```

### 2. Application Debug Logs
```bash
# Prepare debug logs for AI analysis
./pmcli sanitize -i debug.log -t 0.8 -s
```

### 3. CI/CD Pipeline Output
```bash
# Sanitize GitHub Actions output
gh run view 123456789 --log | ./pmcli sanitize
```

### 4. Server Access Logs
```bash
# Clean nginx/apache logs
tail -n 1000 /var/log/nginx/access.log | ./pmcli sanitize
```

### 5. Database Query Logs
```bash
# Reduce repetitive query logs
./pmcli sanitize -i postgres.log -m 5
```

## Best Practices

### For AI Prompts

1. **Always sanitize verbose logs** before pasting into AI chats
2. **Review sanitized output** to ensure important context isn't lost
3. **Adjust threshold** based on your needs (start with default 0.85)
4. **Keep statistics** (`-s`) to understand reduction achieved

### For Security

1. **Always check for sensitive data** (enabled by default)
2. **Review warnings carefully** before proceeding
3. **Consider masking** sensitive values before sanitization
4. **Never share** unsanitized logs with sensitive data

### For Different Log Types

**Application Logs**: Use default settings (0.85 threshold, 3 repetitions)
```bash
./pmcli sanitize -i app.log
```

**System Logs**: More aggressive filtering often helpful
```bash
./pmcli sanitize -i syslog -t 0.75 -m 2
```

**Debug Traces**: Preserve more context
```bash
./pmcli sanitize -i debug.trace -t 0.9 -m 5
```

## Troubleshooting

### Common Issues

**"No content to sanitize"**
- Ensure clipboard has content or file exists
- Check file permissions

**"Too much filtered out"**
- Increase threshold: `./pmcli sanitize -t 0.9`
- Increase minimum repetitions: `./pmcli sanitize -m 5`

**"Not enough filtered"**
- Decrease threshold: `./pmcli sanitize -t 0.7`
- Decrease minimum repetitions: `./pmcli sanitize -m 2`

**"Important lines were filtered"**
- The algorithm preserves unique lines between patterns
- Adjust threshold for better results
- Use preview mode (`-p`) to test settings

### Performance

- Processes ~10,000 lines/second on modern hardware
- Memory usage: ~100MB per million lines
- Larger files may take a moment to process

## Examples Gallery

### Example 1: Database Connection Pool
**Input** (50 lines):
```
[POOL] Creating new connection
[POOL] Connection established: conn_id=1234
[POOL] Creating new connection
[POOL] Connection established: conn_id=1235
[... 46 more similar lines ...]
```

**Output** (4 lines):
```
[POOL] Creating new connection
[POOL] Connection established: conn_id=1234
[... 48 similar connection pool messages filtered ...]
```

### Example 2: REST API Requests
**Input** (100+ lines):
```
GET /api/v1/users 200 OK 45ms
GET /api/v1/users 200 OK 52ms
GET /api/v1/users 200 OK 41ms
POST /api/v1/auth/login 201 Created 120ms
GET /api/v1/users 200 OK 38ms
[... many more ...]
```

**Output** (concise):
```
GET /api/v1/users 200 OK 45ms
GET /api/v1/users 200 OK 52ms
[... 75 similar GET /api/v1/users requests filtered ...]
POST /api/v1/auth/login 201 Created 120ms
```

### Example 3: Mixed Log Levels
**Input**:
```
[DEBUG] Entering function processRequest()
[DEBUG] Validating input parameters
[INFO] Processing user request: id=123
[DEBUG] Entering function processRequest()
[DEBUG] Validating input parameters
[ERROR] Database connection failed
[DEBUG] Entering function processRequest()
[DEBUG] Validating input parameters
```

**Output**:
```
[DEBUG] Entering function processRequest()
[DEBUG] Validating input parameters
[INFO] Processing user request: id=123
[... 2 similar debug sequences filtered ...]
[ERROR] Database connection failed
```

## Integration Tips

### With Task-Master
```bash
# Clean task execution logs before adding to PRD
./pmcli sanitize -i task_output.log | pbcopy
```

### With Browser Extension
1. Copy verbose logs from browser console
2. Run `./pmcli sanitize`
3. Paste cleaned logs into AI chat

### In Scripts
```bash
#!/bin/bash
# Auto-sanitize before copying
function smart_copy() {
    echo "$1" | ./pmcli sanitize
}
```

### Git Hooks
```bash
# .git/hooks/pre-commit
# Warn about verbose logs in commits
if git diff --cached | ./pmcli sanitize -s | grep -q "Size reduction: [5-9][0-9]"; then
    echo "Warning: Commit contains repetitive content that could be sanitized"
fi
```

---

**💡 Pro Tip**: For the best results with AI assistants, always sanitize logs to stay within token limits while preserving all important information. The default settings work well for most cases, but don't hesitate to tune them for your specific logs!