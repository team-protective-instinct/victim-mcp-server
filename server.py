from fastapi import FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel
import subprocess, os, signal

app = FastAPI(title="Victim MCP Server", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "ok", "service": "victim-mcp"}


class BlockIPRequest(BaseModel):
    ip: str
    duration_sec: int = 0

@app.post("/execute/block_ip", operation_id="block_ip",
          summary="Block an IP address using iptables")
def block_ip(req: BlockIPRequest):
    """Block inbound and outbound traffic for the specified IP address."""
    try:
        subprocess.run(["iptables", "-I", "INPUT",  "-s", req.ip, "-j", "DROP"], check=True, capture_output=True)
        subprocess.run(["iptables", "-I", "OUTPUT", "-d", req.ip, "-j", "DROP"], check=True, capture_output=True)
        return {"success": True, "message": f"iptables DROP rule added for {req.ip}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TerminateProcessRequest(BaseModel):
    pid: int

@app.post("/execute/terminate_process", operation_id="terminate_process",
          summary="Terminate a process by PID")
def terminate_process(req: TerminateProcessRequest):
    """Kill a suspicious process using SIGKILL."""
    try:
        os.kill(req.pid, signal.SIGKILL)
        return {"success": True, "message": f"Process {req.pid} terminated"}
    except ProcessLookupError:
        raise HTTPException(status_code=404, detail=f"Process {req.pid} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class QuarantineFileRequest(BaseModel):
    path: str

@app.post("/execute/quarantine_file", operation_id="quarantine_file",
          summary="Move a suspicious file to quarantine")
def quarantine_file(req: QuarantineFileRequest):
    """Move a file to /var/quarantine and remove all permissions."""
    QUARANTINE_DIR = "/var/quarantine"
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    try:
        fname = os.path.basename(req.path)
        dest = os.path.join(QUARANTINE_DIR, fname)
        os.rename(req.path, dest)
        os.chmod(dest, 0o000)
        return {"success": True, "message": f"File quarantined: {req.path} -> {dest}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DisableUserRequest(BaseModel):
    username: str

@app.post("/execute/disable_user_account", operation_id="disable_user_account",
          summary="Lock a user account")
def disable_user(req: DisableUserRequest):
    """Lock a suspicious user account using usermod -L."""
    try:
        subprocess.run(["usermod", "-L", req.username], check=True, capture_output=True)
        return {"success": True, "message": f"Account {req.username} locked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BlockNetworkRequest(BaseModel):
    ip: str
    direction: str = "both"

@app.post("/execute/block_network_traffic", operation_id="block_network_traffic",
          summary="Block network traffic for an IP address")
def block_network(req: BlockNetworkRequest):
    """Block inbound, outbound, or both directions of traffic for an IP."""
    try:
        if req.direction in ("inbound", "both"):
            subprocess.run(["iptables", "-I", "INPUT",  "-s", req.ip, "-j", "DROP"], check=True, capture_output=True)
        if req.direction in ("outbound", "both"):
            subprocess.run(["iptables", "-I", "OUTPUT", "-d", req.ip, "-j", "DROP"], check=True, capture_output=True)
        return {"success": True, "message": f"Traffic blocked for {req.ip} ({req.direction})"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


ALLOWED_SERVICES = {"auditd", "sysmon", "nginx", "postgresql", "filebeat", "ssh", "rsyslog"}

class RestartServiceRequest(BaseModel):
    service_name: str

@app.post("/execute/restart_service", operation_id="restart_service",
          summary="Restart a system service")
def restart_service(req: RestartServiceRequest):
    """Restart an allowed system service (auditd, sysmon, nginx, postgresql, filebeat, ssh, rsyslog)."""
    if req.service_name not in ALLOWED_SERVICES:
        raise HTTPException(status_code=400, detail=f"Service not in allowed list: {ALLOWED_SERVICES}")
    try:
        subprocess.run(["systemctl", "restart", req.service_name], check=True, capture_output=True)
        return {"success": True, "message": f"Service {req.service_name} restarted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MCP 서버 마운트 (FastAPI → MCP 프로토콜)
mcp = FastApiMCP(app)
mcp.mount()
