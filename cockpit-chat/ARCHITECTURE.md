# Cockpit Chat Architecture - Detailed Explanation

---

## How The UI Is Achieved

### Simple Web Components

```
┌─────────────────────────────────┐
│  Header (Title + Status)        │
├─────────────────────────────────┤
│                                 │
│  Messages Container             │
│  (Scrollable)                   │
│    ┌─────────────┐              │
│    │ User msg    │              │
│    └─────────────┘              │
│  ┌─────────────┐                │
│  │ AI msg      │                │
│  └─────────────┘                │
│                                 │
├─────────────────────────────────┤
│  [Input Field]  [Send Button]   │
└─────────────────────────────────┘
```

**Implementation**: Plain HTML + CSS + JavaScript

---

## How Session Context Works

### The Challenge

MCPHost `--quiet` mode is **stateless**:
```bash
mcphost -p "message 1" --quiet  # Process 1 (starts, ends)
mcphost -p "message 2" --quiet  # Process 2 (new, no memory)
```

### The Solution

**Conversation History Pattern**:

```javascript
// JavaScript maintains history
conversationHistory = [
  {role: 'user', content: 'msg1'},
  {role: 'assistant', content: 'response1'},
  {role: 'user', content: 'msg2'}
];

// Each call includes FULL history
function buildPrompt() {
  return conversationHistory.map(msg => 
    `${msg.role === 'user' ? 'User' : 'Assistant'}: ${msg.content}`
  ).join('\n\n');
}

// MCPHost call
mcphost -p "User: msg1\n\nAssistant: response1\n\nUser: msg2" --quiet
```

**Result**: Each MCPHost call sees complete conversation context!

### Example Flow

```
Message 1:
  conversationHistory = []
  User types: "which roles"
  
  Call: mcphost -p "User: which roles"
  Response: "17 roles: aide, firewall..."
  
  conversationHistory = [
    {user: "which roles"},
    {assistant: "17 roles..."}
  ]

Message 2:
  User types: "configure aide at midnight"
  
  Build prompt:
    "User: which roles
     Assistant: 17 roles...
     User: configure aide at midnight"
  
  Call: mcphost -p [full history]
  Response: "I'll configure aide... Proceed?"
  
  conversationHistory = [
    {user: "which roles"},
    {assistant: "17 roles..."},
    {user: "configure aide"},
    {assistant: "Proceed?"}
  ]

Message 3:
  User types: "yes"
  
  Build prompt with ALL history
  
  Call: mcphost -p [full conversation]
  AI sees: "configure aide" + "Proceed?" + "yes"
  AI understands: "yes" = proceed with aide config!
  Response: "Executing..." ✅
```

**Context maintained through history, not persistent process!**

---

**The plugin doesn't bypass this!**

When AI tries to execute a role:
1. MCPHost calls the hook
2. `approver.py` prompts in terminal
3. User must approve in terminal
4. Only then does execution proceed

**UI doesn't get approval - terminal does!** ✅

---

#### Separate Processes

```bash
# Terminal usage
$ mcphost
# Process ID: 67890
# Interactive mode
# Your session

# Cockpit usage (simultaneous)
Browser → cockpit.spawn(['mcphost', '-p', '...', '--quiet'])
# Process ID: 12345
# Batch mode
# Web session
```

**Different PIDs = completely isolated!**

#### No Shared State

| Aspect | Terminal MCPHost | Cockpit MCPHost |
|--------|------------------|-----------------|
| **Process** | 67890 | 12345 (different!) |
| **Mode** | Interactive | --quiet |
| **Session** | Long-lived | Short-lived |
| **State** | In memory | Conversation history |
| **Config** | ~/.mcphost.yml | Same config (read-only) |

**They can both run at the same time!**

---

## Security Analysis

### What The Plugin Can Do

1. **Call mcphost** as the logged-in user
2. **Read mcphost configuration** (if accessible to user)
3. **Display responses** in browser

#### Could it interfere with other mcphost sessions?

**No** - Separate processes:
- Different PIDs
- No shared state
- Configuration read-only
- Independent execution


