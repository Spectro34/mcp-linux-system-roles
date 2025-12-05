#!/usr/bin/env python3
"""
Blocking approval hook for mcphost.
This script BLOCKS until user explicitly approves or denies.
"""
import json
import sys
import os

def get_user_approval():
    """Get user approval (blocking) - reads from /dev/tty."""
    try:
        # Read from /dev/tty to ensure we get user input even if stdin is piped
        with open('/dev/tty', 'r') as tty:
            print("\nApprove this tool execution? [y/N]: ", end='', flush=True, file=sys.stderr)
            response = tty.readline().strip().lower()
            return response in ('y', 'yes')
    except Exception as e:
        print(f"Error reading from terminal: {e}", file=sys.stderr)
        # Fail safe - deny if we can't get user input
        return False

def main():
    try:
        # Validate that we can access /dev/tty before proceeding
        # This ensures we can actually prompt the user
        try:
            test_tty = open('/dev/tty', 'r')
            test_tty.close()
        except Exception as e:
            # If we can't access /dev/tty, we can't get user approval
            # This is a security issue - block execution
            print(f"CRITICAL: Cannot access terminal for approval: {e}", file=sys.stderr)
            print(json.dumps({"decision": "block", "reason": "Cannot access terminal for user approval - execution blocked for security"}))
            sys.exit(1)
        
        # Read hook input from mcphost (first line only)
        line = sys.stdin.readline()
        if not line or line.strip() == '':
            print("CRITICAL: No input received from mcphost", file=sys.stderr)
            print(json.dumps({"decision": "block", "reason": "No input received from mcphost"}))
            sys.exit(1)
            
        input_data = json.loads(line)
        
        tool_name = input_data.get('tool_name', 'unknown')
        tool_input_str = input_data.get('tool_input', '{}')
        
        # Parse tool input
        try:
            tool_input = json.loads(tool_input_str)
        except:
            tool_input = {}
        
        role_name = tool_input.get('role_name', 'unknown_role')
        role_vars = tool_input.get('role_vars', {})
        
        # Show what will be executed (to stderr - visible to user)
        print("\n", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print("⚠️  FINAL CONFIRMATION - Review Variables Before Execution", file=sys.stderr)
        print("="*80, file=sys.stderr)
        print(f"\n  Role: {role_name}", file=sys.stderr)
        print(f"\n  Final variables to be applied:", file=sys.stderr)
        
        # Format variables nicely
        if role_vars:
            for key, value in role_vars.items():
                if isinstance(value, (list, dict)):
                    print(f"    • {key}: {json.dumps(value)}", file=sys.stderr)
                else:
                    print(f"    • {key}: {value}", file=sys.stderr)
        else:
            print("    (no variables)", file=sys.stderr)
        
        print("\n" + "="*80, file=sys.stderr)
        print("⚠️  This will modify your system. Review carefully.", file=sys.stderr)
        print("="*80, file=sys.stderr)
        
        # BLOCKING approval - wait for user input from terminal
        approved = get_user_approval()
        
        if approved:
            print("✓ Approved - Tool will execute", file=sys.stderr)
            print(json.dumps({"decision": "approve"}))
        else:
            print("✗ Denied - Tool execution BLOCKED", file=sys.stderr)
            print(json.dumps({"decision": "block", "reason": "User denied approval"}))
            
    except Exception as e:
        # Fail safe - block on any error
        print(f"Hook error: {e}", file=sys.stderr)
        print(json.dumps({"decision": "block", "reason": f"Hook error: {e}"}))

if __name__ == "__main__":
    main()
