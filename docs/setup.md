# Setup Guide

This guide walks you through setting up the MCP Linux System Roles server step-by-step.

## Prerequisites

### 1. SUSE Linux System Roles

The SUSE roles should already be installed on openSUSE/SLES systems at:
```
/usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/
```

**Verify installation**:
```bash
ls /usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/roles/
```

You should see: aide, firewall, ssh, cockpit, podman, etc.

**If not installed**:
```bash
# This is distribution-specific
# On openSUSE: usually pre-installed
# On RHEL/Fedora: install fedora-linux-system-roles or rhel-system-roles
```

---

### 2. mcphost

Install mcphost (Model Context Protocol host):

```bash
# Follow official instructions at:
# https://github.com/wong2/mcphost

# Example with pip:
pip install mcphost
```

---

### 3. Ollama and Model

Install Ollama and the gpt-oss:20b model:

```bash
# Install ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull gpt-oss:20b
```

**Why gpt-oss:20b?**
- Properly calls MCP tools (doesn't just print JSON)
- Good balance of capability and speed
- Other models like qwen2.5-coder may output JSON text instead of calling tools

---

## Installation Steps

### Step 1: Copy Files

Copy the `mcp-linux-system-roles` directory to your desired location:

```bash
# Example: copy to home directory
cp -r mcp-linux-system-roles ~/mcp-linux-system-roles

# Or to /opt for system-wide installation
sudo cp -r mcp-linux-system-roles /opt/
```

For this guide, we'll assume you copied to `~/mcp-linux-system-roles`.

---

### Step 2: Make Scripts Executable

```bash
chmod +x ~/mcp-linux-system-roles/server/server.py
chmod +x ~/mcp-linux-system-roles/universal_approver.py
```

---

### Step 3: Configure mcphost

#### 3a. Copy Example Config

```bash
cp ~/mcp-linux-system-roles/.mcphost.yml.example ~/.mcphost.yml
```

#### 3b. Edit Paths

Open `~/.mcphost.yml` and replace `<ABSOLUTE_PATH>` with your actual paths:

```yaml
mcpServers:
  roles:
    type: local
    command: ["/home/YOUR_USERNAME/mcp-linux-system-roles/server/server.py"]
    allowedTools: ["run_system_role", "list_available_roles", "get_role_documentation"]

model: "ollama:gpt-oss:20b"
system-prompt: "/home/YOUR_USERNAME/mcp-linux-system-roles/system-prompt.md"
temperature: 0.2
max-tokens: 2048
```

**Replace**:
- `YOUR_USERNAME` with your actual username
- Or use full absolute paths

---

### Step 4: Setup hooks.yml (CRITICAL)

#### 4a. Create mcphost Config Directory

```bash
mkdir -p ~/.config/mcphost/.mcphost
```

#### 4b. Copy Template

```bash
cp ~/mcp-linux-system-roles/.mcphost/hooks.yml ~/.config/mcphost/.mcphost/
```

#### 4c. Edit hooks.yml

Edit `~/.config/mcphost/.mcphost/hooks.yml` and replace `<ABSOLUTE_PATH>` with the full path to `universal_approver.py`:

```bash
# Example: if package is in ~/mcp-linux-system-roles/
sed -i 's|<ABSOLUTE_PATH>|/home/YOUR_USERNAME/mcp-linux-system-roles|g' ~/.config/mcphost/.mcphost/hooks.yml
```

Or manually edit the file to replace `<ABSOLUTE_PATH>` with your actual path.

#### 4d. Verify hooks.yml

```bash
cat ~/.config/mcphost/.mcphost/hooks.yml
```

Verify the path points to the correct location of `universal_approver.py`.

**Why `~/.config/mcphost/.mcphost/`?**
- Most reliable global location for hooks
- Works regardless of where you run mcphost
- mcphost's hook search is complex; this location is always checked

---

### Step 5: Verify Setup

#### 5a. Test Server Manually

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | ~/mcp-linux-system-roles/server/server.py
```

**Expected output**: JSON listing 3 tools (list_available_roles, get_role_documentation, run_system_role)

#### 5b. Test Approver Manually

```bash
echo '{"tool_name":"roles__run_system_role","tool_input":"{}"}' | ~/mcp-linux-system-roles/universal_approver.py
```

**Expected output**: 
- stderr: `[System Role Verification]`, `[Auto-approved]`
- stdout: `{"decision": "approve"}`

---

## File Location Summary

After setup, your files should be:

```
~/.mcphost.yml                              # Main mcphost config
~/.config/mcphost/.mcphost/hooks.yml        # Hooks config

~/mcp-linux-system-roles/
├── server/server.py                        # MCP server
├── universal_approver.py                   # Approver hook
├── system-prompt.md                        # Model instructions
├── .mcphost/hooks.yml                      # (reference copy)
└── docs/                                   # Documentation
```

---

## Common Issues

### Issue 1: "Permission denied" for server.py

**Solution**:
```bash
chmod +x ~/mcp-linux-system-roles/server/server.py
```

---

### Issue 2: mcphost can't find server

**Symptom**: "Failed to start MCP server"

**Solution**: Check the path in `~/.mcphost.yml`:
```yaml
command: ["/home/USER/mcp-linux-system-roles/server/server.py"]  # Must be absolute path
```

Verify:
```bash
ls -la /home/USER/mcp-linux-system-roles/server/server.py
```

---

### Issue 3: Hooks not working

**Symptom**: Approver never runs, no logs in stderr

**Solution 1**: Check hooks.yml location
```bash
ls ~/.config/mcphost/.mcphost/hooks.yml
```

**Solution 2**: Check approver path in hooks.yml
```yaml
command: "/home/USER/mcp-linux-system-roles/universal_approver.py"  # Must be absolute
```

**Solution 3**: Verify matcher names
```bash
# In mcphost, type: /tools
# Check actual tool names shown
# Update matchers in hooks.yml if needed
```

---

### Issue 4: Model outputs JSON instead of calling tool

**Symptom**: Model prints `{"name": "roles__run_system_role", ...}` as text

**Solutions**:
1. **Wrong model**: Switch to `ollama:gpt-oss:20b` in `.mcphost.yml`
2. **Wrong prompt**: Verify `system-prompt` path in `.mcphost.yml`
3. **Model confusion**: Restart mcphost

---

### Issue 5: "Role not found" error

**Symptom**: `the role 'suse.linux_system_roles.aide' was not found`

**Solution**: Verify SUSE collection exists
```bash
ls /usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/roles/aide
```

If not found, you may need to install it or use a different namespace (fedora, rhel).

---

## Verification Checklist

Before first use, verify:

- [ ] `server.py` is executable
- [ ] `universal_approver.py` is executable
- [ ] `~/.mcphost.yml` has correct absolute paths
- [ ] `~/.config/mcphost/.mcphost/hooks.yml` exists and has correct path
- [ ] SUSE roles exist at `/usr/share/ansible/collections/.../suse/linux_system_roles/`
- [ ] Ollama is running: `ollama list` shows `gpt-oss:20b`
- [ ] Manual server test works (step 5a above)
- [ ] Manual approver test works (step 5b above)

---

## Next Steps

Once setup is complete, proceed to `usage.md` to learn how to use the system.
