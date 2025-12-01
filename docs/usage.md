# Usage Guide

This guide explains how to use the MCP Linux System Roles server in mcphost.

## Starting mcphost

```bash
mcphost
```

**Expected output**:
```
Model loaded: ollama (gpt-oss:20b)
Model loaded successfully on GPU
Loaded 4 tools from MCP servers
```

The "4 tools" should be:
- `roles_list_available_roles` (or `roles__list_available_roles`)
- `roles_get_role_documentation`
- `roles_run_system_role` (or `roles__run_system_role`)
- `roles_get_role_status`

---

## Basic Workflow

### 1. List Available Roles

**User input**:
```
show available roles
```

**Model response**:
```
Available SUSE Linux System Roles:
  - suse.linux_system_roles.aide
  - suse.linux_system_roles.certificate
  - suse.linux_system_roles.cockpit
  - suse.linux_system_roles.crypto_policies
  - suse.linux_system_roles.firewall
  - suse.linux_system_roles.ha_cluster
  - suse.linux_system_roles.journald
  - suse.linux_system_roles.keylime_server
  - suse.linux_system_roles.mssql
  - suse.linux_system_roles.podman
  - suse.linux_system_roles.postfix
  - suse.linux_system_roles.selinux
  - suse.linux_system_roles.squid
  - suse.linux_system_roles.ssh
  - suse.linux_system_roles.suseconnect
  - suse.linux_system_roles.systemd
  - suse.linux_system_roles.timesync
```

---

### 2. Execute a Role

#### Example 1: Configure AIDE

**User**:
```
run aide and schedule checks for noon
```

**Model** (calls `get_role_documentation("aide")` internally):
```
To schedule AIDE checks at noon, I will use:
• aide_init: true
• aide_cron_check: true  
• aide_cron_interval: "0 12 * * *"

Shall I proceed with these settings?
```

**User**:
```
yes
```

**Model** (calls `run_system_role`, approver logs and approves, Ansible runs):
```
[Shows Ansible playbook output]

The AIDE role completed successfully:
• AIDE database initialized
• Cron job configured to run at noon daily
• No errors reported
```

**Verify**:
```bash
sudo cat /etc/crontab | grep aide
# Output: 0 12 * * * root /usr/bin/aide --check
```

---

#### Example 2: Configure Cockpit

**User**:
```
enable cockpit web console on port 9090
```

**Model** (reads cockpit documentation):
```
To enable the Cockpit web console, I will use:
• cockpit_enabled: true
• cockpit_port: 9090

Shall I proceed?
```

**User**:
```
yes
```

**Model** (executes):
```
Cockpit web console configured successfully. Access at https://localhost:9090
```

---

#### Example 3: Configure Journald

**User**:
```
set journal max file size to 100M and keep 7 days of logs
```

**Model** (reads journald documentation):
```
To configure journal size and retention, I will use:
• journald_system_max_use: "1G"
• journald_system_keep_free: "2G" 
• journald_max_file_sec: "1day"
• journald_max_retention_sec: "7day"

Shall I proceed?
```

**User**:
```
yes
```

**Model** (executes):
```
Journald configured successfully. Logs will be kept for 7 days with appropriate size limits.
```

---

#### Example 4: Configure SSH Server

**User**:
```
disable password authentication for ssh
```

**Model** (reads ssh documentation):
```
To disable password authentication, I will use:
• ssh_PasswordAuthentication: "no"

Shall I proceed?
```

**User**:
```
yes
```

**Model** (executes):
```
SSH configured successfully. Password authentication disabled.
```

---

### 3. Get Role Documentation

You can explicitly ask the model to show you a role's documentation:

**User**:
```
show me the documentation for the cockpit role
```

**Model** (calls `get_role_documentation("cockpit")`):
```
[Displays cockpit role README]

# Cockpit Role

This role installs and configures Cockpit web console.

## Variables

### cockpit_enabled
Whether to enable and start cockpit.socket
Type: bool

### cockpit_port
Port for the web console (default: 9090)
Type: int

[... full documentation ...]
```

---

## Understanding the Confirmation Workflow

The system enforces a **two-step confirmation** for safety:

```
1. User makes request
   ↓
2. Model reads role documentation
   ↓
3. Model proposes variables
   "I will use X, Y, Z. Shall I proceed?"
   ↓
4. User confirms: "yes"
   ↓
5. Model calls run_system_role tool
   ↓
6. Approver logs execution (shown in terminal)
   ↓
7. Ansible playbook executes
   ↓
8. Model summarizes results
```

**Why this workflow?**
- **Step 3-4**: User reviews variables before execution
- **Step 6**: Audit trail of what was executed
- **No double confirmation**: User doesn't need to approve twice (once in chat is enough)

---

## Terminal Output

When a role executes, you'll see this in the **terminal** (not mcphost chat):

```
[System Role Verification]
Executing role suse.linux_system_roles.aide with vars:
{
  "aide_init": true,
  "aide_cron_check": true,
  "aide_cron_interval": "0 12 * * *"
}
[Auto-approved - user confirmed in chat]
```

This is the **approver logging** the execution for your audit trail.

---

## Advanced Usage

### Viewing Full Playbook Output

The model typically summarizes Ansible output. To see the full output, ask:

**User**:
```
run aide and show me the full ansible output
```

The model will include the complete stdout/stderr from Ansible.

---

### Multiple Variables

You can specify complex configurations:

**User**:
```
initialize aide, run a check, and schedule daily checks at midnight
```

**Model**:
```
I will use:
• aide_init: true
• aide_check: true
• aide_cron_check: true
• aide_cron_interval: "0 0 * * *"

Shall I proceed?
```

---

### Asking for Clarification

If the model doesn't know a variable name, it will read the documentation:

**User**:
```
configure postfix as a relay
```

**Model** (reads postfix docs):
```
To configure Postfix as a relay, I will use:
• postfix_relayhost: "<your_relay_server>"

What relay server should I use?
```

**User**:
```
smtp.example.com
```

**Model**:
```
I will use:
• postfix_relayhost: "smtp.example.com"

Shall I proceed?
```

---

## Available Slash Commands

In mcphost, you can use these commands:

### `/tools`
Shows all available tools and their schemas.

```
/tools
```

### `/help`
Shows mcphost help.

```
/help
```

### `/clear`
Clears conversation history.

```
/clear
```

---

## Example Sessions

### Session 1: Complete AIDE Setup

```
You: what can aide do?

Model: AIDE (Advanced Intrusion Detection Environment) monitors file 
       integrity. It can initialize a database, run checks, and 
       schedule periodic scans.

You: initialize aide and schedule for noon

Model: I will use:
       • aide_init: true
       • aide_cron_check: true
       • aide_cron_interval: "0 12 * * *"
       Shall I proceed?

You: yes

Model: [Executes]
       AIDE configured successfully:
       • Database initialized at /var/lib/aide/aide.db
       • Cron job created to run at noon daily
       • Verify with: sudo cat /etc/crontab
```

---

### Session 2: Cockpit and Journald Configuration

```
You: list available roles

Model: [Shows 17 roles]

You: enable cockpit and configure journald to keep logs for 30 days

Model: [Reads cockpit docs]
       I'll configure two roles:
       
       1. Cockpit: cockpit_enabled=true, cockpit_port=9090
       2. Journald: journald_max_retention_sec="30day"
       
       Shall I proceed?

You: yes

Model: [Executes both roles]
       Cockpit enabled at https://localhost:9090
       Journald configured with 30-day retention.
```

---

## Troubleshooting

### Model Doesn't Call Tool

**Symptom**: Model prints JSON like `{"name": "roles__run_system_role", ...}` instead of calling it.

**Solution**:
1. Verify model is `gpt-oss:20b` in `.mcphost.yml`
2. Restart mcphost
3. Try rephrasing: "run the aide role" instead of "execute aide"

---

### Approver Doesn't Run

**Symptom**: No `[System Role Verification]` message in terminal.

**Solution**:
1. Check `~/.config/mcphost/.mcphost/hooks.yml` exists
2. Verify paths in hooks.yml are absolute
3. Test manually: `echo '{"tool_name":"roles__run_system_role","tool_input":"{}"}' | ~/mcp-linux-system-roles/universal_approver.py`

---

### Role Fails to Execute

**Symptom**: Ansible returns error like "role not found".

**Solution**:
1. Verify role exists: `ls /usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/roles/`
2. Check logs in mcphost for exact error
3. Try with a different role to isolate the issue

---

### Cron Job Not Created

**Symptom**: After running AIDE, `sudo cat /etc/crontab` doesn't show the job.

**Common causes**:
1. **Task said "ok" not "changed"**: Job may already exist from previous run
2. **Permission issue**: Verify playbook ran as root (should by default)
3. **Wrong location**: Job is in `/etc/crontab`, not user crontab

**Debug**:
```bash
# Check /etc/crontab
sudo cat /etc/crontab | grep aide

# Check systemd timers (if your distro uses those instead)
systemctl list-timers | grep aide
```

---

## Best Practices

1. **Always review variables** before confirming
2. **Check terminal output** for approver logs
3. **Verify changes** after execution (e.g., `sudo cat /etc/crontab`)
4. **Start simple** - test with AIDE before trying complex roles
5. **Read documentation** - ask model to show role docs if unsure

---

## Next Steps

- Review `architecture.md` to understand how the system works
- Check available roles and their capabilities
- Experiment with different roles and configurations
