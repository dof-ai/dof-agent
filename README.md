# dof-agent
Physical AI MCP Agent

## Getting Started

This agent is designed to be used in VS Code to connect to a robotics simulator.

### Prerequisites

Make sure the `mcp` package is installed in the Python environment of your cloud instance.

```bash
/isaac-sim/python.sh -m pip install mcp
```

### MCP Server Configuration

To connect the agent to your robotics simulator (e.g., NVIDIA Isaac Sim), you need to configure an MCP server.

#### For Cursor Users

1.  If you don't have one, create a `.cursor` directory in the root of your project.
2.  Inside this directory, create a file named `mcp.json`.
3.  Add the following content to `mcp.json`:

    ```json
    {
        "mcpServers": {
            "dof-sim": {
                "command": "/isaac-sim/python.sh",
                "args": [
                    "/root/Documents/src/server.py"
                ]
            }
        }
    }
    ```

#### For VS Code Users

1.  If you don't have one, create a `.vscode` directory in the root of your project.
2.  Inside this directory, create or open your `settings.json` file.
3.  Add the following `mcp` configuration to your `settings.json`:

    ```json
    {
        "mcp": {
            "inputs": [],
            "servers": {
                "dof-sim": {
                    "command": "/isaac-sim/python.sh",
                    "args": [
                        "/root/Documents/src/server.py"
                    ],
                    "env": {}
                }
            }
        }
    }
    ```
    
    If your `settings.json` file already has content, add the `"mcp"` configuration within the main JSON object.