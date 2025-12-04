# Cockpit Chat - Generic MCPHost Interface

A minimal, generic Cockpit plugin that provides a web-based chat interface to MCPHost.

## Installation

Use the Ansible playbook from the parent directory:

```bash
cd /home/spectro/github/test-antigravity/mcp-linux-system-roles/mcp-linux-system-roles

# Configure Cockpit UI
ansible-playbook -i localhost, -c local cockpit_ui.yml
```

This will:
- ✅ Ensure Cockpit is installed and running
- ✅ Create user Cockpit plugins directory
- ✅ Symlink this plugin as "system-roles"
- ✅ Verify all plugin files

## Access

https://localhost:9090 → "System Roles"

## Features

- **Generic** - Adapts to whatever mcphost is configured with
- **Minimal** - ~280 lines of code
- **Conversation history** - Maintains context
- **Clean UI** - Simple chat interface

## How It Works

### Calls MCPHost with Conversation History

```javascript
// Maintains conversation in JavaScript
conversationHistory = [
  {role: 'user', content: 'message1'},
  {role: 'assistant', content: 'response1'},
  {role: 'user', content: 'message2'}
];

// Each call includes full history for context
cockpit.spawn(['mcphost', '-p', fullHistory, '--quiet', '--config', CONFIG]);
```

### Uses Parent Configuration

- **Config**: `../.mcphost.yml`
- **MCP Server**: `../server/server.py`  
- **System Prompt**: `../system-prompt.md`
- **Approval Hooks**: `../.mcphost/hooks.yml`

**Plugin is generic - parent project manages all configuration!**

## Files

```
cockpit-chat/
├── manifest.json     # Cockpit plugin metadata
├── index.html        # Simple UI structure
├── chat.css          # Clean styling
├── chat.js           # Generic mcphost interface
├── README.md         # This file
└── ARCHITECTURE.md   # Technical details
```

## Security

- ✅ Uses parent project's mcphost configuration
- ✅ Approval hooks work (terminal prompts)
- ✅ Runs as Cockpit user (no escalation)
- ✅ Same security as terminal mcphost

## No Interference

- ✅ Separate processes from terminal mcphost
- ✅ Can run simultaneously
- ✅ No conflicts

## Documentation

- This file: `README.md`
- Technical details: `ARCHITECTURE.md`
- Parent project: `../README.md`
- Deployment: `../cockpit_ui.yml`
