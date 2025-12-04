# Architecture Documentation

This document explains each component of the MCP Linux System Roles server and how they work together.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     User (via mcphost)                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              AI Model (gpt-oss:20b)                              │
│  Reads: system-prompt.md for instructions                       │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Tools (server.py)                         │
│  • list_available_roles                                         │
│  • get_role_documentation                                       │
│  • run_system_role ──► universal_approver.py                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              Ansible (SUSE Linux System Roles)                   │
│  /usr/share/ansible/collections/ansible_collections/            │
│      suse/linux_system_roles/roles/                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Descriptions

### 1. `server/server.py`

**Purpose**: MCP server that exposes Linux System Roles as tools for the AI model.

**What it does**:
- Listens for JSON-RPC requests from mcphost on stdin
- Provides 4 tools to the AI model:
  1. `list_available_roles` - Lists all installed SUSE roles
  2. `get_role_documentation` - Reads role README files
  3. `run_system_role` - Executes Ansible playbooks with user-specified variables and returns execution results to the model

**Key Functions**:
```python
def list_tools()
    # Defines the 4 MCP tools available to the model

def handle_call_tool(name, arguments)
    # Routes tool calls to appropriate handlers
    # - list_available_roles: scans /usr/share/ansible/.../roles/
    # - get_role_documentation: reads README.md files
    # - run_system_role: calls run_ansible()
    
def run_ansible(role_name, vars_dict)
    # Creates temporary playbook
    # Runs ansible-playbook command
    # Returns stdout/stderr and status
```

**Communication Protocol**: JSON-RPC 2.0 over stdin/stdout

---

### 2. `universal_approver.py`

**Purpose**: Approver hook that logs role execution for auditing.

**What it does**:
- Receives tool call details from mcphost before execution
- Logs which role is being executed with what variables to stderr
- Automatically approves (since user already confirmed in chat)
- Allows the tool to proceed to server.py

**Why it exists**:
The two-step confirmation workflow is:
1. Model asks user in chat: "Shall I proceed with these settings?"
2. User responds "yes" in chat
3. Model calls `run_system_role` tool
4. Approver intercepts → logs → approves
5. Tool executes

This provides an audit trail while keeping the UX smooth.

**Input** (from mcphost via stdin):
```json
{
  "tool_name": "roles__run_system_role",
  "tool_input": "{\"role_name\": \"suse.linux_system_roles.aide\", \"role_vars\": {...}}"
}
```

**Output** (to mcphost via stdout):
```json
{"decision": "approve"}
```

**Logs to stderr**:
```
[System Role Verification]
Executing role suse.linux_system_roles.aide with vars:
{
  "aide_init": true
}
[Auto-approved - user confirmed in chat]
```

---

### 3. `.mcphost/hooks.yml` (template provided)

**Purpose**: Template for mcphost hooks configuration.

**What to do**: Copy this file to `~/.config/mcphost/.mcphost/hooks.yml` and update the path.

**Location after setup**: `~/.config/mcphost/.mcphost/hooks.yml` (global)

**Template content**:
```yaml
hooks:
  PreToolUse:
    - matcher: "roles_run_system_role"
      hooks:
        - type: command
          command: "<ABSOLUTE_PATH>/universal_approver.py"
          timeout: 300
    - matcher: "roles__run_system_role"
      hooks:
        - type: command
          command: "<ABSOLUTE_PATH>/universal_approver.py"
          timeout: 300
```

**Setup**: Replace `<ABSOLUTE_PATH>` with the full path to the package directory.

**Why two matchers?**
Different models may namespace tools differently (single vs double underscore). Both are covered.

**Setup instructions**: See `docs/setup.md` for complete steps.

---

### 4. `system-prompt.md`

**Purpose**: Instructions for the AI model on how to use the tools.

**What it does**:
- Defines the model's role: "Linux System Roles Assistant"
- Enforces the two-step confirmation workflow
- Instructs the model to read documentation before suggesting variables
- Provides role naming convention (`suse.linux_system_roles.<role>`)

**Key Sections**:

**Safety Rules**:
```markdown
Before calling any tool that modifies the system, you MUST:
- List the exact variables and values you intend to use
- Ask for explicit confirmation
- STOP and wait for "yes"
- Do NOT call any tool until user confirms
```

**Documentation Workflow**:
```markdown
Before suggesting variables for ANY role, you MUST:
1. Call get_role_documentation with the role's short name
2. Read and understand the variables
3. Then propose appropriate variables
```

**Example**:
```markdown
User: "enable cockpit web console"
You: Call get_role_documentation(role_name="cockpit")
You: Read variables, then suggest
You: "I will enable cockpit on port 9090. Shall I proceed?"
User: "yes"
You: Call run_system_role(...)
```

---

### 5. `.mcphost.yml.example`

**Purpose**: Template configuration for mcphost.

**What it does**:
- Defines the MCP server connection
- Specifies which tools are allowed
- Sets the AI model and system prompt

**Structure**:
```yaml
mcpServers:
  roles:  # Server name (becomes namespace prefix)
    type: local  # Run as local process
    command: ["/path/to/server.py"]  # How to start server
    allowedTools:  # Which tools the model can use
      - run_system_role
      - list_available_roles
      - get_role_documentation

model: "ollama:gpt-oss:20b"  # AI model to use
system-prompt: "/path/to/system-prompt.md"  # Model instructions
temperature: 0.2  # Deterministic responses
max-tokens: 2048  # Response length limit
```

**File Location**: 
- Copy to `~/.mcphost.yml` or
- Copy to your project directory as `.mcphost.yml`

---

## Data Flow Example

**User Request**: "run aide schedule for noon"

```
1. User types request in mcphost
   ↓
2. Model reads system-prompt.md
   - Recognizes this is an AIDE request
   ↓
3. Model calls: get_role_documentation("aide")
   - server.py reads /usr/share/.../aide/README.md
   - Returns: documentation with variables
   ↓
4. Model analyzes documentation
   - Identifies: aide_cron_check, aide_cron_interval
   ↓
5. Model proposes to user:
   "I will use: aide_cron_check=true, aide_cron_interval='0 12 * * *'"
   "Shall I proceed?"
   ↓
6. User types: "yes"
   ↓
7. Model calls: run_system_role(...)
   ↓
8. mcphost checks hooks.yml
   - Finds matcher for "roles__run_system_role"
   - Runs: universal_approver.py
   ↓
9. universal_approver.py
   - Logs to stderr: [Executing role aide...]
   - Returns: {"decision": "approve"}
   ↓
10. mcphost forwards to server.py
    ↓
11. server.py
    - Creates temporary playbook
    - Runs: ansible-playbook /tmp/playbook.yml
    - Returns: stdout, stderr, status
    ↓
12. Model summarizes for user:
    "AIDE configured successfully. Cron job created at noon."
```

---

## File Locations Summary

| File | Production Location | Purpose |
|------|-------------------|---------|
| `server/server.py` | Anywhere (specify in .mcphost.yml) | MCP server process |
| `universal_approver.py` | Anywhere (specify in hooks.yml) | Pre-execution logging |
| `hooks.yml` | **`~/.config/mcphost/.mcphost/hooks.yml`** (must create manually) | Hook configuration |
| `system-prompt.md` | Anywhere (specify in .mcphost.yml) | Model instructions |
| `.mcphost.yml` | `~/.mcphost.yml` or project directory | Main configuration |

**Note**: `hooks.yml` is NOT included in this package and must be created manually during setup.

---

## Security Notes

1. **Ansible runs as root** (via `become: True` in playbook)
   - Only install this on systems you trust
   - Review role variables before confirming

2. **Approver auto-approves**
   - User confirmation happens in chat (step 6 above)
   - Approver logs execution for audit trail
   - No additional terminal prompt needed

3. **Model has full access** to all allowed tools
   - Only use with trusted models
   - Review system-prompt.md to understand model's capabilities
