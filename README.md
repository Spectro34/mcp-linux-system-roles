# MCP Server for Linux System Roles

An MCP (Model Context Protocol) server that enables AI models to configure Linux systems using SUSE Linux System Roles through Ansible.

## Features

- ✅ **17 SUSE Roles**: aide, firewall, ssh, cockpit, podman, selinux, squid, and more
- ✅ **Dynamic Documentation**: Model reads role README files to learn variables
- ✅ **User Verification**: Safe two-step confirmation workflow
- ✅ **Auto-approval**: Approver logs execution but doesn't block (user confirms in chat)
- ✅ **Complete Execution**: Runs Ansible playbooks and returns results

## Architecture

```
User Request
    ↓
Model (gpt-oss:20b via mcphost)
    ↓
MCP Tools:
  - list_available_roles → Lists all 17 SUSE roles
  - get_role_documentation → Reads role README
  - run_system_role → Executes Ansible playbook
    ↓
universal_approver.py (logs and auto-approves)
    ↓
server.py (runs ansible-playbook)
    ↓
SUSE Linux System Roles (Ansible)
    ↓
System Configuration Applied
```

## Installation

## Quick Start

**Automated setup** (recommended):
```bash
ansible-playbook -i localhost, -c local setup.yml
```

See [QUICKSTART.md](QUICKSTART.md) for details.

**Manual setup**: See [docs/setup.md](docs/setup.md)

### Prerequisites

```bash
# Install SUSE Linux System Roles
# (Usually pre-installed on openSUSE/SLES)
# Collection is at: /usr/share/ansible/collections/ansible_collections/suse/linux_system_roles

# Install mcphost
# Follow instructions at: https://github.com/wong2/mcphost

# Install ollama and model
ollama pull gpt-oss:20b
```

### Setup

1. **Clone/copy this directory** to your desired location

2. **Update `.mcphost.yml.example`**:
   - Copy to your mcphost config directory or home directory as `.mcphost.yml`
   - Replace `<ABSOLUTE_PATH>` with the full path to this directory
   ```yaml
   command: ["/home/user/mcp-linux-system-roles/server/server.py"]
   system-prompt: "/home/user/mcp-linux-system-roles/system-prompt.md"
   ```

3. **Update hooks.yml**:
   - In `.mcphost/hooks.yml`, update the approver path:
   ```yaml
   command: "/home/user/mcp-linux-system-roles/universal_approver.py"
   ```

4. **Make scripts executable**:
   ```bash
   chmod +x server/server.py universal_approver.py
   ```

5. **Copy hooks to mcphost config**:
   ```bash
   mkdir -p ~/.config/mcphost/.mcphost
   cp .mcphost/hooks.yml ~/.config/mcphost/.mcphost/
   # Or wherever your mcphost config directory is
   ```

## Usage

### Start mcphost

```bash
mcphost
```

### Example Interactions

**List available roles:**
```
You: show available roles
Model: [Shows 17 SUSE roles]
```

**Configure AIDE:**
```
You: run aide and schedule checks for noon
Model: [Reads AIDE documentation]
Model: I will use: aide_init=True, aide_cron_check=True, aide_cron_interval="0 12 * * *"
      Shall I proceed?
You: yes
Model: [Executes playbook, shows results]
```

**Configure Cockpit:**
```
You: enable cockpit web console
Model: [Reads cockpit documentation]
Model: I will enable cockpit on port 9090. Shall I proceed?
You: yes
Model: [Configures cockpit]
```

## File Structure

```
mcp-linux-system-roles/
├── server/
│   └── server.py              # MCP server (handles tools)
├── .mcphost/
│   └── hooks.yml              # Template (copy to global config)
├── universal_approver.py       # Approver (logs execution)
├── system-prompt.md           # Model instructions
├── .mcphost.yml.example       # Example config
├── docs/
│   ├── architecture.md        # Technical documentation
│   ├── setup.md              # Installation guide
│   └── usage.md              # Usage examples
└── README.md                 # This file
```

## How It Works

### 1. User Request
User asks for a system configuration in natural language.

### 2. Documentation Lookup
Model calls `get_role_documentation` to read the role's README and learn about available variables.

### 3. Variable Proposal
Model proposes specific variables based on the documentation and asks for confirmation.

### 4. User Confirmation
User responds "yes" in the chat.

### 5. Tool Execution
Model calls `run_system_role` → Approver logs it → Ansible executes → Results returned.

## Tools Available

| Tool | Description |
|------|-------------|
| `list_available_roles` | Lists all 17 SUSE Linux System Roles |
| `get_role_documentation` | Reads role README to learn variables |
| `run_system_role` | Executes Ansible playbook with specified variables |
| `get_role_status` | Placeholder for status checks |

## Available SUSE Roles

1. aide - Intrusion detection
2. certificate - Certificate management
3. cockpit - Web-based admin interface
4. crypto_policies - System crypto policies
5. firewall - Firewall configuration
6. ha_cluster - High availability clustering
7. journald - Journal configuration
8. keylime_server - TPM-based attestation
9. mssql - Microsoft SQL Server
10. podman - Container management
11. postfix - Mail server
12. selinux - SELinux configuration
13. squid - Proxy server
14. ssh - SSH server/client config
15. suseconnect - SUSE registration
16. systemd - Systemd configuration
17. timesync - Time synchronization

## Demo
Run `asciinema play demo.cast` to start demo ensure asciinema is installed.

## Troubleshooting

### Model outputs JSON instead of calling tool
- Ensure you're using `gpt-oss:20b` (not qwen or other models)
- Check that `system-prompt.md` path is correct in `.mcphost.yml`

### Approver not running
- Verify hooks.yml path is correct
- Check that universal_approver.py is executable
- Ensure tool name matches in hooks.yml (both `roles_run_system_role` and `roles__run_system_role`)

### Role not found
- Verify SUSE collection exists: `ls /usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/roles/`
- Use `list_available_roles` to see what's installed

### Cron jobs not visible
- System roles add to `/etc/crontab`, not user crontab
- Check with: `sudo cat /etc/crontab`

## License

Apache 2.0
