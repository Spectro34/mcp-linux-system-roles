# Quick Setup Guide

This playbook automates the entire MCP server setup process.

## Prerequisites

- Ansible installed (`sudo zypper install ansible` on openSUSE)
- SUSE Linux System Roles (usually pre-installed on openSUSE/SLES)

## Quick Start

Run from the package directory:

```bash
ansible-playbook -i localhost, -c local setup.yml
```

This will:
1. ✅ Verify SUSE Linux System Roles are installed
2. ✅ Copy MCP server files to `~/mcp-linux-system-roles/`
3. ✅ Create `~/.mcphost.yml` with correct paths
4. ✅ Create `~/.config/mcphost/.mcphost/hooks.yml` with correct paths
5. ✅ Set executable permissions
6. ✅ Verify installation

## Custom Installation Directory

To install to a different location:

```bash
ansible-playbook -i localhost, -c local setup.yml -e "install_dir=/opt/mcp-linux-system-roles"
```

## After Setup

1. **Install Ollama** (if not already installed):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Pull the model**:
   ```bash
   ollama pull gpt-oss:20b
   ```

3. **Install mcphost**:
   ```bash
   # Follow instructions at: https://github.com/wong2/mcphost
   ```

4. **Start mcphost**:
   ```bash
   mcphost
   ```

5. **Test**:
   ```
   show available roles
   ```

## What Gets Installed

```
~/mcp-linux-system-roles/
├── server/server.py
├── universal_approver.py
├── system-prompt.md
├── docs/
│   ├── architecture.md
│   ├── setup.md
│   └── usage.md
└── README.md

~/.mcphost.yml                      # Main config
~/.config/mcphost/.mcphost/hooks.yml # Hooks config
```

## Troubleshooting

### "SUSE roles not found"
Install with:
```bash
sudo zypper install ansible-collection-suse-suse_roles
```

### Playbook fails with permissions error
Make sure you're running as your regular user (not root):
```bash
ansible-playbook -i localhost, -c local setup.yml
```

### Want to reinstall
Remove the old installation first:
```bash
rm -rf ~/mcp-linux-system-roles ~/.mcphost.yml ~/.config/mcphost/.mcphost/hooks.yml
ansible-playbook -i localhost, -c local setup.yml
```

## Manual Setup

If you prefer manual setup or the playbook doesn't work, see `docs/setup.md` for step-by-step instructions.
