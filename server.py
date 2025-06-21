import paramiko
from mcp.server.fastmcp import FastMCP
import logging
import os
from fastapi import FastAPI, HTTPException, Request
import threading
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Starting server")

mcp = FastMCP("ssh")

# Create FastAPI app
app = FastAPI()

app.mount("/", mcp.sse_app())

class SSHSessionManager:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def get_session(self, session_id):
        with self.lock:
            return self.sessions.get(session_id)

    def create_session(self, session_id, **ssh_kwargs):
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(**ssh_kwargs)
            self.sessions[session_id] = client
            return client

    def close_session(self, session_id):
        with self.lock:
            if session_id in self.sessions:
                self.sessions[session_id].close()
                del self.sessions[session_id]

ssh_manager = SSHSessionManager()

@mcp.tool()
def ssh_start_session(
    session_id: str,
    username: str = "alex",
    password: str = "your-pass"
):
    """
    Starts or restarts an SSH session to the local machine.

    Parameters:
        session_id (str): Unique identifier for the session (e.g., user or conversation id).
        username (str): SSH username (default: 'alex').
        password (str): SSH password (default: 'your-pass').

    Returns:
        dict: {"status": "ok"} if successful, or error details.

    LLM Usage:
        Use this tool to start or restart an SSH session before running commands.
        Provide a unique session_id for each user or conversation.
    """
    try:
        client = ssh_manager.create_session(
            session_id,
            hostname="localhost",
            username=username,
            password=password
        )
        logger.info(f"Started SSH session for {session_id}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to start SSH session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
def ssh_exec_command(
    session_id: str,
    command: str,
    input_data: Optional[str] = None,
    get_pty: bool = False
):
    """
    Executes a command on the local machine via SSH, optionally sending interactive input.

    Parameters:
        session_id (str): The session id returned by ssh_start_session.
        command (str): The shell command to execute.
        input_data (str, optional): Input to send to the command if it prompts for interaction (e.g., sudo password, 'Y' for prompts).
        get_pty (bool, optional): Whether to request a pseudo-terminal (required for some sudo commands).

    Returns:
        dict: {"output": "..."} with the command output, or error details.

    LLM Usage:
        Use this tool to run shell commands on the local machine.
        If the command is interactive, provide the required input in input_data.
        Set get_pty=True when running sudo commands that require terminal access.
    """
    logger.info(f"Restoring session {session_id}")
    client = ssh_manager.get_session(session_id)
    if not client:
        logger.info(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        logger.info(f"Executing command on session {session_id}")
        
        # Check if command contains sudo and automatically use get_pty and -S option
        if "sudo " in command and "-S" not in command and not get_pty:
            logger.info(f"Command contains sudo, adjusting for proper execution")
            
            # If input_data is provided (password), modify command to use -S
            if input_data:
                if "sudo " in command:
                    # Replace first instance of sudo with sudo -S
                    command = command.replace("sudo ", "sudo -S ", 1)
                    get_pty = True
        
        # Execute command with proper options
        stdin, stdout, stderr = client.exec_command(command, get_pty=get_pty)
        
        if input_data:
            stdin.write(input_data + '\n')
            stdin.flush()
        
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        logger.info(f"Command output for {session_id}: {output}")
        if error:
            logger.error(f"Command error for {session_id}: {error}")
        
        return {"output": output, "error": error}
    except Exception as e:
        logger.error(f"SSH exec error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@mcp.tool()
def ssh_exec_sudo_command(
    session_id: str,
    command: str,
    password: str = "your-pass"
):
    """
    Executes a sudo command with proper terminal handling.

    Parameters:
        session_id (str): The session id returned by ssh_start_session.
        command (str): The shell command to execute (without 'sudo').
        password (str): The sudo password.

    Returns:
        dict: {"output": "..."} with the command output, or error details.

    LLM Usage:
        Use this tool to run sudo commands that require elevated privileges.
        The command should NOT include 'sudo' - it will be added automatically.
    """
    logger.info(f"Executing sudo command on session {session_id}")
    
    # Prepend sudo -S to the command
    sudo_command = f"sudo -S {command}"
    
    # Call ssh_exec_command with the sudo command
    return ssh_exec_command(
        session_id=session_id,
        command=sudo_command,
        input_data=password,
        get_pty=True
    )

@mcp.tool()
def ssh_close_session(
    session_id: str
):
    """
    Closes an existing SSH session.

    Parameters:
        session_id (str): The session id to close.

    Returns:
        dict: {"status": "closed"} if successful.

    LLM Usage:
        Use this tool to close the SSH session when finished.
    """
    ssh_manager.close_session(session_id)
    logger.info(f"Closed SSH session for {session_id}")
    return {"status": "closed"}
