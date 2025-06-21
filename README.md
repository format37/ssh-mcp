# ssh-mcp

SSH MCP server that provides secure shell access to local machines through a Model Context Protocol interface.

## Overview

This server implements an SSH client using Paramiko and exposes SSH functionality through MCP tools, allowing AI assistants to execute commands on local machines securely.

## Features

- **Session Management**: Create, manage, and close SSH sessions with unique session IDs
- **Command Execution**: Execute shell commands with proper input handling
- **Sudo Support**: Specialized tools for running privileged commands with password authentication
- **Interactive Commands**: Support for commands requiring user input (e.g., sudo prompts)
- **Thread-Safe**: Concurrent session management with proper locking

## Tools

- `ssh_start_session`: Initialize SSH connection to localhost
- `ssh_exec_command`: Execute shell commands with optional input
- `ssh_exec_sudo_command`: Run sudo commands with automatic password handling
- `ssh_close_session`: Clean up SSH sessions

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   ./start.sh
   ```

The server runs on `http://0.0.0.0:7777` and provides an SSE (Server-Sent Events) endpoint for MCP communication.

## Configuration

Default SSH credentials:
- Hostname: localhost
- Username: alex
- Password: your-pass

**Note**: Update these credentials in `server.py` for production use.

## Claude-desktop config
If using Linux, your config folder is:
```
/home/username/.config/Claude/claude_desktop_config.json
```
To enable this u need to enable it in claude desktop: File / Config / Developer / Edit config

## SSH Daemon:
Configure ssh daemon:
```
nano /etc/systemd/system/ssh-mcp.service
```
Paste (update ur username):
```
[Unit]                                                                                                                                                                                                                                                         
Description=SSH MCP Server                                                                                                                                                                                                                                     
After=network.target                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                               
[Service]                                                                                                                                                                                                                                                      
User=alex                                                                                                                                                                                                                                                      
WorkingDirectory=/home/alex/projects/ssh-mcp
ExecStart=/bin/bash -c 'eval "$(/home/alex/anaconda3/bin/conda shell.bash hook)" && conda activate base && /home/alex/anaconda3/bin/uvicorn server:app --host 0.0.0.0 --port 7777'
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```
Start
```
sudo systemctl daemon-reload
sudo systemctl enable ssh-mcp.service
sudo systemctl start ssh-mcp.service
```