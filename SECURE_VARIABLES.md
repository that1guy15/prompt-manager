# 🔐 Secure Variables Documentation

## Overview

Secure Variables provide encrypted storage for sensitive information like API keys, passwords, and tokens. They integrate seamlessly with the Prompt Manager while maintaining the highest security standards.

## Key Security Features

✅ **AES-256 Encryption** - Industry-standard encryption at rest  
✅ **Session-based Authentication** - Time-limited access (1 hour default)  
✅ **Write-only Storage** - Values cannot be retrieved in plaintext via CLI after creation  
✅ **Runtime-only Decryption** - Secrets only decrypted when actually used in prompts  
✅ **Visual Indicators** - Clear distinction with 🔒 icons in listings  
✅ **Audit Logging** - Complete trail of all secure variable operations  
✅ **System Keychain Integration** - Leverages macOS Keychain for password storage  

## Quick Start

### 1. Add a Secure Variable
```bash
# Interactive mode (recommended)
./pmcli svar add github_token "GitHub API token for CI/CD"

# With value provided (less secure - visible in shell history)
./pmcli svar add api_key "OpenAI API Key" --value "sk-1234567890..."
```

### 2. List Variables (shows both regular and secure)
```bash
./pmcli var list
```

Output:
```
Name                 Description                              Default         Used Type    
-------------------------------------------------------------------------------------------
endpoint             API endpoint URL                         /api/v1/users   4    REGULAR
🔒 github_token      GitHub API token for CI/CD              •••••••••••••••  2    SECURE  
🔒 api_key           OpenAI API Key                           None            0    SECURE  
```

### 3. Use in Prompts
Secure variables work automatically in prompt rendering:

```bash
# Will use secure variables if available, prompt for authentication if needed
./pmcli copy 1 

# Override secure variable with temporary value
./pmcli copy 1 -v api_key="temporary_override"
```

## Command Reference

### Secure Variable Management

```bash
# Add new secure variable
./pmcli svar add <name> "<description>" [--default "default_value"]

# List all secure variables  
./pmcli svar list [--show-values]  # DANGEROUS: shows actual values

# Update secure variable
./pmcli svar update <name> [-d "new description"] [--value] [--default "new_default"]

# Delete secure variable
./pmcli svar delete <name> [-f]  # -f for force without confirmation
```

### Session Management

```bash
# Check authentication status
./pmcli svar session info

# End secure session
./pmcli svar session logout  

# Extend session time
./pmcli svar session extend
```

### Audit & Export

```bash
# View audit log
./pmcli svar audit [-n 50]  # Show last 50 entries

# Export encrypted backup
./pmcli svar export backup.json
```

## Security Best Practices

### 1. Password Management
- Choose a strong password (8+ characters)
- Don't use your system password
- Password is never stored - only a secure hash
- Uses PBKDF2 with 100,000 iterations

### 2. Session Management
- Default session timeout: 1 hour
- Configure with `PM_SECURE_SESSION_TTL` environment variable
- Sessions automatically expire for security
- Use `./pmcli svar session logout` when done

### 3. Value Handling
- Values are write-only after creation
- Runtime-only decryption during prompt use
- No plaintext storage anywhere on disk
- Secure deletion from memory after use

### 4. Storage Security
- Encrypted with AES-256 (or fallback encryption)
- Stored separately from regular variables
- File permissions restricted to owner only (600)
- Uses system keychain when available (macOS)

## Configuration

### Environment Variables
```bash
# Session timeout in minutes (default: 60)
export PM_SECURE_SESSION_TTL=120

# Prompt API URL (if using API mode)
export PROMPT_API_URL="https://your-server.com/api"
```

### Config File (~/.pm_config.json)
```json
{
  "secure_session_ttl_minutes": 60,
  "encryption_backend": "auto"
}
```

## Integration Examples

### 1. API Testing Prompt
```
Test the {endpoint} API:
Authorization: Bearer {api_token}
Method: {method}
Expected: {expected_response}
```

Variables:
- `endpoint` (regular): `/api/v1/users`  
- `api_token` (secure): `sk-1234567890...`
- `method` (regular): `GET`
- `expected_response` (regular): `{"users": []}`

### 2. Database Connection
```
Connect to database:
Host: {db_host}
Username: {db_user} 
Password: {db_password}
Database: {db_name}
```

Variables:
- `db_host` (regular): `localhost`
- `db_user` (regular): `app_user`
- `db_password` (secure): `super_secret_password`
- `db_name` (regular): `myapp_production`

## Troubleshooting

### Common Issues

**"Authentication failed"**
- Check if you're using the correct password
- Session may have expired - check with `./pmcli svar session info`

**"Variable 'X' is secure and requires authentication"**
- Run `./pmcli svar session info` to check authentication status
- Authenticate with any secure variable command

**"Encryption capability not available"**
- Install `cryptography` package: `pip install cryptography`
- Falls back to less secure encryption if unavailable

**"Permission denied" errors**
- Check file permissions on secure data files
- Ensure proper ownership of `~/.pm_secure_hash`

### Getting Help

```bash
# Command help
./pmcli svar --help
./pmcli svar add --help

# Debug encryption
python3 test_secure_vars.py
```

## File Locations

- **Regular variables**: `prompts.json`
- **Secure variables**: `prompts_secure.json` (encrypted)
- **Password hash**: `~/.pm_secure_hash` or macOS Keychain
- **Session data**: `/tmp/.pm_secure_session` (temporary)
- **Config**: `~/.pm_config.json` (optional)

## Migration from Regular Variables

To convert a regular variable to secure:

1. Note the current value: `./pmcli var list`
2. Delete regular variable: `./pmcli var delete <name>`  
3. Add as secure variable: `./pmcli svar add <name> "description"`
4. Update any prompts if needed

## Advanced Usage

### Browser Extension Integration
Secure variables work seamlessly with the browser extension, with authentication prompts appearing as needed.

### API Integration  
When using the API server, secure variables require authentication headers and follow the same security model.

### Backup & Recovery
Export encrypted backups regularly:
```bash
./pmcli svar export "backup-$(date +%Y%m%d).json"
```

Restore is manual - re-add variables from your secure documentation.

---

**Remember**: Secure variables are designed for sensitive data. Use regular variables for non-sensitive configuration that needs to be easily shareable or visible.