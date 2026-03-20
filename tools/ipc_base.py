#!/usr/bin/env python3
"""
IPC Abstraction Layer for Code Execution Tool

Provides cross-platform IPC transport:
- Unix domain sockets on Linux/macOS
- Named pipes on Windows
- TCP fallback for systems without native support
"""

import abc
import json
import logging
import platform
import socket
import sys
import threading
import time
import uuid
from typing import Any, Callable, Optional, Dict

logger = logging.getLogger(__name__)

_IS_WINDOWS = platform.system() == "Windows"


class IPCBase(abc.ABC):
    """Abstract base class for IPC transports."""
    
    @abc.abstractmethod
    def listen(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Start listening for incoming connections and call callback with messages."""
        pass
    
    @abc.abstractmethod
    def connect(self) -> bool:
        """Connect as a client. Returns True on success."""
        pass
    
    @abc.abstractmethod
    def send(self, data: Dict[str, Any]) -> None:
        """Send data to the other end."""
        pass
    
    @abc.abstractmethod
    def recv(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive data from the other end. Returns None on timeout."""
        pass
    
    @abc.abstractmethod
    def close(self) -> None:
        """Close the connection."""
        pass
    
    @abc.abstractmethod
    def get_endpoint(self) -> str:
        """Get the endpoint identifier (socket path or pipe name)."""
        pass


class UnixDomainSocket(IPCBase):
    """Unix domain socket implementation for Linux/macOS."""
    
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.listening = False
        self.connection_thread: Optional[threading.Thread] = None
        
    def listen(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Start listening for connections."""
        try:
            # Clean up any existing socket file
            import os
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            # Create server socket
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(1)
            self.listening = True
            
            def connection_handler():
                while self.listening:
                    try:
                        self.server_socket.settimeout(1.0)
                        conn, _ = self.server_socket.accept()
                        conn.settimeout(0.1)  # Non-blocking for recv
                        
                        while self.listening:
                            try:
                                data = conn.recv(4096)
                                if not data:
                                    break
                                
                                message = json.loads(data.decode('utf-8'))
                                callback(message)
                            except socket.timeout:
                                continue
                            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                                logger.error(f"Invalid message received: {e}")
                                break
                            except Exception as e:
                                logger.error(f"Error in connection handler: {e}")
                                break
                        conn.close()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.listening:  # Only log if not shutting down
                            logger.error(f"Error accepting connection: {e}")
                        break
            
            self.connection_thread = threading.Thread(target=connection_handler, daemon=True)
            self.connection_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start Unix domain socket listener: {e}")
            raise
    
    def connect(self) -> bool:
        """Connect to the Unix domain socket."""
        try:
            self.client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.client_socket.connect(self.socket_path)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Unix domain socket: {e}")
            return False
    
    def send(self, data: Dict[str, Any]) -> None:
        """Send data over the socket."""
        if not self.client_socket:
            raise RuntimeError("Not connected")
        
        message = json.dumps(data).encode('utf-8')
        self.client_socket.sendall(message)
    
    def recv(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive data from the socket."""
        if not self.client_socket:
            raise RuntimeError("Not connected")
        
        self.client_socket.settimeout(timeout)
        try:
            data = self.client_socket.recv(4096)
            if not data:
                return None
            return json.loads(data.decode('utf-8'))
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
            return None
    
    def close(self) -> None:
        """Close the socket."""
        self.listening = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=1.0)
        
        # Clean up socket file
        try:
            import os
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
        except:
            pass
    
    def get_endpoint(self) -> str:
        """Get the socket path."""
        return self.socket_path


class TCPLocalhost(IPCBase):
    """TCP localhost fallback for systems without native IPC."""
    
    def __init__(self, port: Optional[int] = None):
        self.port = port or self._find_free_port()
        self.host = "127.0.0.1"
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.listening = False
        self.connection_thread: Optional[threading.Thread] = None
        self.auth_token = str(uuid.uuid4())
    
    @staticmethod
    def _find_free_port() -> int:
        """Find a free port on localhost."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
    
    def listen(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Start listening for connections."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.listening = True
            
            def connection_handler():
                while self.listening:
                    try:
                        self.server_socket.settimeout(1.0)
                        conn, addr = self.server_socket.accept()
                        
                        # Verify connection is from localhost
                        if addr[0] != self.host:
                            logger.warning(f"Rejected connection from {addr}")
                            conn.close()
                            continue
                        
                        conn.settimeout(0.1)
                        
                        # First message should be auth token
                        auth_data = self._recv_message(conn)
                        if not auth_data or auth_data.get('auth_token') != self.auth_token:
                            logger.warning("Invalid auth token")
                            conn.close()
                            continue
                        
                        # Send acknowledgement
                        self._send_message(conn, {'status': 'authenticated'})
                        
                        # Handle subsequent messages
                        while self.listening:
                            try:
                                message = self._recv_message(conn)
                                if message:
                                    callback(message)
                            except socket.timeout:
                                continue
                            except Exception as e:
                                logger.error(f"Error in message handler: {e}")
                                break
                        conn.close()
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if self.listening:
                            logger.error(f"Error accepting connection: {e}")
                        break
            
            self.connection_thread = threading.Thread(target=connection_handler, daemon=True)
            self.connection_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start TCP listener: {e}")
            raise
    
    def connect(self) -> bool:
        """Connect to the TCP server."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            
            # Send auth token
            self._send_message(self.client_socket, {'auth_token': self.auth_token})
            
            # Wait for acknowledgement
            response = self._recv_message(self.client_socket)
            return response and response.get('status') == 'authenticated'
            
        except Exception as e:
            logger.error(f"Failed to connect to TCP server: {e}")
            return False
    
    def send(self, data: Dict[str, Any]) -> None:
        """Send data over TCP."""
        if not self.client_socket:
            raise RuntimeError("Not connected")
        
        self._send_message(self.client_socket, data)
    
    def recv(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive data from TCP."""
        if not self.client_socket:
            raise RuntimeError("Not connected")
        
        self.client_socket.settimeout(timeout)
        return self._recv_message(self.client_socket)
    
    def _send_message(self, sock: socket.socket, data: Dict[str, Any]) -> None:
        """Send a JSON message with length prefix."""
        message = json.dumps(data).encode('utf-8')
        length = len(message)
        sock.sendall(length.to_bytes(4, 'big') + message)
    
    def _recv_message(self, sock: socket.socket) -> Optional[Dict[str, Any]]:
        """Receive a JSON message with length prefix."""
        try:
            # Read length prefix
            length_data = sock.recv(4)
            if not length_data:
                return None
            length = int.from_bytes(length_data, 'big')
            
            # Read message
            message = b''
            while len(message) < length:
                chunk = sock.recv(length - len(message))
                if not chunk:
                    return None
                message += chunk
            
            return json.loads(message.decode('utf-8'))
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return None
    
    def close(self) -> None:
        """Close the TCP connection."""
        self.listening = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=1.0)
    
    def get_endpoint(self) -> str:
        """Get the TCP endpoint."""
        return f"tcp://{self.host}:{self.port}"


def get_ipc_transport(transport_type: str = "auto") -> IPCBase:
    """
    Get the best available IPC transport for the current platform.
    
    Args:
        transport_type: "auto", "uds", "named_pipe", or "tcp"
    
    Returns:
        An IPC transport instance
    """
    if transport_type == "auto":
        if _IS_WINDOWS:
            # Try named pipes first, fall back to TCP
            try:
                from .ipc_windows import WindowsNamedPipe
                return WindowsNamedPipe(f"hermes-rpc-{uuid.uuid4().hex[:8]}")
            except ImportError:
                logger.warning("Windows named pipes not available, using TCP fallback")
                return TCPLocalhost()
        else:
            # Use Unix domain sockets on POSIX systems
            import tempfile
            socket_path = f"{tempfile.gettempdir()}/hermes-rpc-{uuid.uuid4().hex}"
            return UnixDomainSocket(socket_path)
    
    elif transport_type == "uds" and not _IS_WINDOWS:
        import tempfile
        socket_path = f"{tempfile.gettempdir()}/hermes-rpc-{uuid.uuid4().hex}"
        return UnixDomainSocket(socket_path)
    
    elif transport_type == "named_pipe" and _IS_WINDOWS:
        from .ipc_windows import WindowsNamedPipe
        return WindowsNamedPipe(f"hermes-rpc-{uuid.uuid4().hex[:8]}")
    
    elif transport_type == "tcp":
        return TCPLocalhost()
    
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")


def check_ipc_availability() -> Dict[str, Any]:
    """
    Check which IPC transports are available on this system.
    
    Returns:
        Dict with availability information
    """
    result = {
        "platform": platform.system(),
        "uds_available": not _IS_WINDOWS,
        "named_pipes_available": False,
        "tcp_available": True,
        "recommended": "uds"
    }
    
    if _IS_WINDOWS:
        try:
            import win32pipe
            result["named_pipes_available"] = True
            result["recommended"] = "named_pipe"
        except ImportError:
            result["recommended"] = "tcp"
    
    return result
