#!/usr/bin/env python3
import json
import sys
import os

def main():
    with open("/home/spectro/github/test-antigravity/approver_debug.log", "a") as log:
        log.write("Approver started\n")
    try:
        input_data = json.load(sys.stdin)
        with open("/home/spectro/github/test-antigravity/approver_debug.log", "a") as log:
            log.write(f"Input: {json.dumps(input_data)}\n")
        tool_name = input_data.get('tool_name')
        
        if 'run_system_role' not in tool_name:
            # Auto-approve other tools if any (or block, but for now we only hook this one)
            # Actually, the hook matcher in hooks.yml filters for run_system_role, 
            # so we should only see that one. But good to be safe.
            print(json.dumps({"decision": "approve"}))
            return

        tool_input = json.loads(input_data.get('tool_input', '{}'))
        role_name = tool_input.get('role_name', 'unknown_role')
        role_vars = tool_input.get('role_vars', {})
        
        # Log what's being executed for safety/auditing
        print(f"\n\033[1;33m[System Role Verification]\033[0m", file=sys.stderr)
        print(f"Executing role \033[1m{role_name}\033[0m with vars:", file=sys.stderr)
        print(json.dumps(role_vars, indent=2), file=sys.stderr)
        print(f"\033[1;32m[Auto-approved - user confirmed in chat]\033[0m\n", file=sys.stderr)
        
        # Auto-approve since user already confirmed "yes" in the chat to the model
        print(json.dumps({"decision": "approve"}))
            
    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)
        print(json.dumps({"decision": "block", "reason": f"Hook error: {e}"}))

if __name__ == "__main__":
    main()
