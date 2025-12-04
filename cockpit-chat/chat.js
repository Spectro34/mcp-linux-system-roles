console.log('System Roles Chat Interface');

// Configuration - Absolute paths
const MCPHOST_CONFIG = '/home/spectro/github/test-antigravity/mcp-linux-system-roles/mcp-linux-system-roles/.mcphost.yml';
const WORKING_DIR = '/home/spectro/github/test-antigravity/mcp-linux-system-roles/mcp-linux-system-roles';

let conversationHistory = [];

// DOM elements
const messages = document.getElementById('messages');
const input = document.getElementById('input');
const sendBtn = document.getElementById('send');
const status = document.getElementById('status');

// Add message to UI
function addMessage(text, type = 'assistant') {
  const msg = document.createElement('div');
  msg.className = `message ${type}`;
  
  const content = document.createElement('div');
  content.className = 'message-content';
  
  // Handle formatting
  if (type === 'assistant') {
    let formatted = text
      .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    content.innerHTML = formatted;
  } else {
    content.textContent = text;
  }
  
  msg.appendChild(content);
  messages.appendChild(msg);
  messages.scrollTop = messages.scrollHeight;
}

// Update status indicator
function setStatus(state) {
  status.className = `status ${state}`;
}

// Call MCPHost with conversation history for context
async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  
  addMessage(text, 'user');
  conversationHistory.push({role: 'user', content: text});
  input.value = '';
  
  setStatus('thinking');
  sendBtn.disabled = true;
  
  try {
    // Build conversation context
    let prompt = '';
    conversationHistory.forEach(msg => {
      const role = msg.role === 'user' ? 'User' : 'Assistant';
      prompt += `${role}: ${msg.content}\n\n`;
    });
    
    console.log('Calling MCPHost with history');
    
    const result = await callMCPHost(prompt.trim());
    
    addMessage(result, 'assistant');
    conversationHistory.push({role: 'assistant', content: result});
    
    setStatus('connected');
  } catch (error) {
    console.error('Error:', error);
    addMessage('Error: ' + (error.message || error), 'error');
    setStatus('connected');
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

// Call MCPHost with absolute paths
function callMCPHost(conversationText) {
  return new Promise((resolve, reject) => {
    console.log('Spawning mcphost with config:', MCPHOST_CONFIG);
    
    // Call mcphost with absolute config path and working directory
    const proc = cockpit.spawn(['mcphost', '-p', conversationText, '--quiet', '--config', MCPHOST_CONFIG], {
      err: 'out',
      directory: WORKING_DIR
    });
    
    let output = '';
    
    proc.stream(data => {
      output += data;
    });
    
    proc.done(() => {
      console.log('MCPHost response received');
      // Clean up ANSI codes
      const cleaned = output
        .replace(/\x1b\[[0-9;]*m/g, '')
        .replace(/\r\n/g, '\n')
        .replace(/\r/g, '\n')
        .trim();
      resolve(cleaned);
    });
    
    proc.fail(err => {
      console.error('MCPHost failed:', err);
      reject(err);
    });
  });
}

// Event listeners
sendBtn.addEventListener('click', sendMessage);

input.addEventListener('keypress', e => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendMessage();
  }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  console.log('System Roles Chat Interface initialized');
  console.log('Using pure MCPHost responses - no hardcoded messages');
  setStatus('connected');
  // No hardcoded greeting - let MCPHost handle all responses
  input.focus();
});
