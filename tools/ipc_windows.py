#!/usr/bin/env python3
"""
Windows Named Pipe Implementation for IPC

Provides Windows-specific IPC transport using named pipes.
Equivalent to Unix domain sockets on Linux/macOS.
"""

import json
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import pywin32 components
try:
    import win32pipe
    import win32file
    import win32event
    import win32security
    import win32con
    import winerror
    import win32api
    import pywintypes
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    logger.warning("pywin32 not available - Windows named pipes will not work")


class WindowsNamedPipe:
    """
    Windows named pipe implementation of IPC transport.
    
    Uses pywin32 to create and manage named pipes for inter-process communication.
    Provides security through ACLs and authentication tokens.
    """
    
    def __init__(self, pipe_name: str):
        if not PYWIN32_AVAILABLE:
            raise RuntimeError("pywin32 is required for Windows named pipes")
        
        self.pipe_name = pipe_name
        self.full_pipe_name = f"\\\\.\\pipe\\{pipe_name}"
        self.pipe_handle: Optional[pywintypes.HANDLE] = None
        self.client_handle: Optional[pywintypes.HANDLE] = None
        self.listening = False
        self.connection_thread: Optional[threading.Thread] = None
        self.auth_token = str(uuid.uuid4())
        self.buffer_size = 4096
        self._stop_event = threading.Event()
        
    def _create_security_attributes(self) -> pywintypes.SECURITY_ATTRIBUTES:
        """
        Create security attributes that only allow the current user to access the pipe.
        """
        # Get current user SID
        user_sid = win32security.GetTokenInformation(
            win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32security.TOKEN_QUERY),
            win32security.TokenUser
        )[0]
        
        # Create ACL that allows full access to current user only
        acl = win32security.ACL()
        acl.AddAccessAllowedAce(
            win32security.ACL_REVISION,
            win32con.GENERIC_ALL,
            user_sid
        )
        
        # Create security descriptor
        sd = win32security.SECURITY_DESCRIPTOR()
        sd.SetSecurityDescriptorOwner(user_sid, False)
        sd.SetSecurityDescriptorGroup(user_sid, False)
        sd.SetSecurityDescriptorDacl(1, acl, 0)
        
        # Create security attributes
        sa = win32security.SECURITY_ATTRIBUTES()
        sa.SECURITY_DESCRIPTOR = sd
        return sa
    
    def listen(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Start listening for client connections."""
        try:
            # Create security attributes for restricted access
            sa = self._create_security_attributes()
            
            def connection_handler():
                while not self._stop_event.is_set():
                    try:
                        # Create named pipe
                        self.pipe_handle = win32pipe.CreateNamedPipe(
                            self.full_pipe_name,
                            win32pipe.PIPE_ACCESS_DUPLEX,
                            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                            1,  # Max instances
                            self.buffer_size,  # Out buffer size
                            self.buffer_size,  # In buffer size
                            0,  # Default timeout
                            sa
                        )
                        
                        # Wait for client connection
                        logger.info(f"Waiting for connection on {self.full_pipe_name}")
                        win32pipe.ConnectNamedPipe(self.pipe_handle, self._stop_event)
                        
                        if self._stop_event.is_set():
                            break
                        
                        self.listening = True
                        
                        # Handle authentication
                        auth_success = self._handle_authentication()
                        if not auth_success:
                            win32file.CloseHandle(self.pipe_handle)
                            self.pipe_handle = None
                            continue
                        
                        # Send authentication acknowledgement
                        self._send_message({'status': 'authenticated'})
                        
                        # Handle messages
                        while not self._stop_event.is_set():
                            try:
                                message = self._recv_message()
                                if message:
                                    callback(message)
                            except Exception as e:
                                logger.error(f"Error handling message: {e}")
                                break
                        
                    except pywintypes.error as e:
                        if e.winerror != winerror.ERROR_BROKEN_PIPE and not self._stop_event.is_set():
                            logger.error(f"Pipe error: {e}")
                    finally:
                        if self.pipe_handle:
                            try:
                                win32file.CloseHandle(self.pipe_handle)
                            except:
                                pass
                            self.pipe_handle = None
                            self.listening = False
            
            self.connection_thread = threading.Thread(target=connection_handler, daemon=True)
            self.connection_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start named pipe listener: {e}")
            raise
    
    def _handle_authentication(self) -> bool:
        """Handle client authentication."""
        try:
            # Read auth token from client
            auth_data = self._recv_message()
            if not auth_data or auth_data.get('auth_token') != self.auth_token:
                logger.warning("Invalid auth token received")
                return False
            return True
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return False
    
    def connect(self) -> bool:
        """Connect to a named pipe as a client."""
        try:
            # Wait for pipe to be available
            for attempt in range(50):  # Wait up to 5 seconds
                try:
                    self.client_handle = win32file.CreateFile(
                        self.full_pipe_name,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0,
                        None,
                        win32file.OPEN_EXISTING,
                        0,
                        None
                    )
                    break
                except pywintypes.error as e:
                    if e.winerror == winerror.ERROR_PIPE_BUSY:
                        # Wait and retry
                        win32event.Sleep(100)
                        continue
                    else:
                        raise
            else:
                raise TimeoutError("Timed out waiting for pipe")
            
            # Send authentication token
            self._send_message({'auth_token': self.auth_token})
            
            # Wait for authentication response
            response = self._recv_message()
            return response and response.get('status') == 'authenticated'
            
        except Exception as e:
            logger.error(f"Failed to connect to named pipe: {e}")
            return False
    
    def _send_message(self, data: Dict[str, Any]) -> None:
        """Send a message over the named pipe."""
        message = json.dumps(data).encode('utf-8')
        
        if self.pipe_handle:  # Server side
            win32file.WriteFile(self.pipe_handle, message)
        elif self.client_handle:  # Client side
            win32file.WriteFile(self.client_handle, message)
        else:
            raise RuntimeError("Not connected to named pipe")
    
    def _recv_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the named pipe."""
        try:
            if self.pipe_handle:  # Server side
                result, data = win32file.ReadFile(self.pipe_handle, self.buffer_size)
            elif self.client_handle:  # Client side
                result, data = win32file.ReadFile(self.client_handle, self.buffer_size)
            else:
                raise RuntimeError("Not connected to named pipe")
            
            if not data:
                return None
            
            # Named pipes preserve message boundaries, so we can decode directly
            return json.loads(data.decode('utf-8'))
            
        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_BROKEN_PIPE:
                return None  # Client disconnected
            elif e.winerror == winerror.ERROR_MORE_DATA:
                # Message too large, need to read more
                logger.warning("Message too large for buffer")
                return None
            else:
                logger.error(f"Error reading from pipe: {e}")
                return None
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Invalid message received: {e}")
            return None
    
    def send(self, data: Dict[str, Any]) -> None:
        """Send data to the other end."""
        self._send_message(data)
    
    def recv(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive data with timeout."""
        # Note: Named pipes don't have a simple timeout mechanism like sockets
        # We'll use a polling approach with small sleeps
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            message = self._recv_message()
            if message is not None:
                return message
            time.sleep(0.01)  # Small sleep to prevent busy waiting
        
        return None
    
    def close(self) -> None:
        """Close the named pipe."""
        self._stop_event.set()
        self.listening = False
        
        # Force disconnect any client
        if self.pipe_handle:
            try:
                win32file.CloseHandle(self.pipe_handle)
            except:
                pass
            self.pipe_handle = None
        
        if self.client_handle:
            try:
                win32file.CloseHandle(self.client_handle)
            except:
                pass
            self.client_handle = None
        
        # Wait for connection thread to finish
        if self.connection_thread and self.connection_thread.is_alive():
            self.connection_thread.join(timeout=1.0)
        
        # Clean up the pipe
        try:
            # Try to delete the pipe (this might fail if still in use)
            win32file.DeleteFile(self.full_pipe_name)
        except:
            pass
    
    def get_endpoint(self) -> str:
        """Get the pipe endpoint."""
        return self.full_pipe_name


# Compatibility shim for when pywin32 is not available
class MockWindowsNamedPipe:
    """Mock implementation that raises an error when pywin32 is not available."""
    
    def __init__(self, pipe_name: str):
        raise RuntimeError(
            "Windows named pipes require pywin32. Install with: pip install pywin32\n"
            "Or use TCP fallback by setting transport_type='tcp'"
        )


# Export the right class based on availability
if PYWIN32_AVAILABLE:
    WindowsNamedPipe = WindowsNamedPipe
else:
    WindowsNamedPipe = MockWindowsNamedPipe
