#!/usr/bin/env python3
import json
import sys
import subprocess
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("mcp-server-linux-roles")

def run_ansible(role_name, vars_dict):
    """Runs the specified ansible role with the given variables."""
    
    # Construct the playbook dynamically
    playbook_content = [
        {
            "hosts": "localhost",
            "connection": "local",
            "become": True,
            "tasks": [
                {
                    "name": f"Include {role_name} role",
                    "include_role": {
                        "name": role_name
                    },
                    "vars": vars_dict
                }
            ]
        }
    ]
    
    # Write temporary playbook
    playbook_path = f"/tmp/{role_name.replace('.', '_')}_playbook.yml"
    with open(playbook_path, "w") as f:
        json.dump(playbook_content, f)

    cmd = ["ansible-playbook", playbook_path]
    env = os.environ.copy()
    
    logger.info(f"Running role {role_name} with vars: {vars_dict}")
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        return {"status": "success", "stdout": result.stdout}
    except subprocess.CalledProcessError as e:
        # Generic Error Handling
        response = {"status": "error", "stderr": e.stderr, "stdout": e.stdout, "rc": e.returncode}

        # SPECIAL HANDLING FOR AIDE
        # AIDE uses specific return codes for "changes found" (success in a check context)
        if "aide" in role_name:
             # Check for integrity violation (RC 7 or specific output)
             if '"rc": 7' in e.stdout or "AIDE found differences" in e.stdout:
                 response["status"] = "integrity_violation"
                 response["message"] = "AIDE found differences between the database and the filesystem."
                 return response
             
             # Check for update success (RC 4 or specific output)
             if '"rc": 4' in e.stdout or "New AIDE database written" in e.stdout:
                 response["status"] = "updated"
                 response["message"] = "AIDE database updated successfully."
                 return response

        logger.error(f"Ansible failed: {e.stderr}")
        return response

def list_tools():
    return [
        {
            "name": "run_system_role",
            "description": "Configure and execute a Linux System Role (e.g., aide, firewall, network).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "role_name": {
                        "type": "string",
                        "description": "The namespaced name of the role (e.g., 'suse.linux_system_roles.aide', 'rhel.system_roles.firewall')."
                    },
                    "role_vars": {
                        "type": "object",
                        "description": "Dictionary of variables to pass to the role. Keys must match the role's variable names."
                    }
                },
                "required": ["role_name", "role_vars"]
            }
        },
        {
            "name": "list_available_roles",
            "description": "List all available Linux System Roles installed on the system.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_role_documentation",
            "description": "Get the README documentation for a specific SUSE Linux System Role to understand its variables and usage.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "role_name": {
                        "type": "string",
                        "description": "The short name of the role (e.g., 'aide', 'firewall', 'ssh')"
                    }
                },
                "required": ["role_name"]
            }
        }
    ]

def handle_call_tool(name, arguments):
    # Log relative to the server script location
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server_debug.log")
    with open(log_path, "a") as log:
        log.write(f"Server called: {name} args: {arguments}\n")
    
    if name.endswith("list_available_roles"):
        try:
            # List only SUSE roles from the system-wide collection
            suse_path = "/usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/roles"
            if os.path.exists(suse_path):
                roles = os.listdir(suse_path)
                roles_list = "\n".join([f"  - suse.linux_system_roles.{role}" for role in sorted(roles) if not role.startswith('.')])
                return {"content": [{"type": "text", "text": f"Available SUSE Linux System Roles:\n{roles_list}"}]}
            else:
                return {"content": [{"type": "text", "text": "SUSE Linux System Roles collection not found at /usr/share/ansible/collections/"}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error listing roles: {str(e)}"}]}
    
    if name.endswith("get_role_documentation"):
        role_name = arguments.get("role_name")
        if not role_name:
            return {"content": [{"type": "text", "text": "Error: role_name is required"}]}
        
        # Read README.md for the specified role
        readme_path = f"/usr/share/ansible/collections/ansible_collections/suse/linux_system_roles/roles/{role_name}/README.md"
        
        if not os.path.exists(readme_path):
            return {"content": [{"type": "text", "text": f"Documentation not found for role '{role_name}'. Use list_available_roles to see available roles."}]}
        
        try:
            with open(readme_path, 'r') as f:
                content = f.read()
            # Return first 8000 chars to avoid token limits
            if len(content) > 8000:
                content = content[:8000] + "\n\n... (truncated, see full documentation at " + readme_path + ")"
            return {"content": [{"type": "text", "text": content}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error reading documentation: {str(e)}"}]}

    if name.endswith("run_system_role"):
        role_name = arguments.get("role_name")
        role_vars = arguments.get("role_vars", {})
        
        if not role_name:
            return {"content": [{"type": "text", "text": "Error: role_name is required"}]}

        return {"content": [{"type": "text", "text": json.dumps(run_ansible(role_name, role_vars), indent=2)}]}
    
    raise ValueError(f"Unknown tool: {name}")

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            request = json.loads(line)
            if request.get("jsonrpc") != "2.0":
                continue
                
            method = request.get("method")
            msg_id = request.get("id")
            
            response = {
                "jsonrpc": "2.0",
                "id": msg_id
            }
            
            try:
                if method == "initialize":
                    response["result"] = {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "mcp-server-linux-roles", "version": "0.1.0"}
                    }
                elif method == "notifications/initialized":
                    continue
                elif method == "tools/list":
                    response["result"] = {"tools": list_tools()}
                elif method == "tools/call":
                    params = request.get("params", {})
                    name = params.get("name")
                    args = params.get("arguments", {})
                    response["result"] = handle_call_tool(name, args)
                else:
                    continue
            except Exception as e:
                response["error"] = {"code": -32603, "message": str(e)}
                logger.exception("Error handling request")
            
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
            continue
        except Exception as e:
            logger.exception("Fatal error in main loop")
            break

if __name__ == "__main__":
    main()
