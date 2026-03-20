#!/usr/bin/env python3
"""
Unit tests for Windows IPC implementations.

Tests both Unix domain sockets and Windows named pipes
to ensure cross-platform compatibility.
"""

import json
import os
import sys
import tempfile
import threading
import time
import uuid
import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.ipc_base import (
    UnixDomainSocket,
    TCPLocalhost,
    get_ipc_transport,
    check_ipc_availability
)

# Import Windows named pipes if available
try:
    from tools.ipc_windows import WindowsNamedPipe
    WINDOWS_PIPES_AVAILABLE = True
except ImportError:
    WINDOWS_PIPES_AVAILABLE = False


class TestIPCAvailability:
    """Test IPC availability checking."""
    
    def test_check_ipc_availability(self):
        """Test that IPC availability check returns expected structure."""
        result = check_ipc_availability()
        
        assert "platform" in result
        assert "uds_available" in result
        assert "named_pipes_available" in result
        assert "tcp_available" in result
        assert "recommended" in result
        
        # TCP should always be available
        assert result["tcp_available"] is True


class TestTCPLocalhost:
    """Test TCP localhost implementation."""
    
    def test_tcp_creation(self):
        """Test TCP transport creation."""
        tcp = TCPLocalhost()
        assert tcp.port > 0
        assert tcp.host == "127.0.0.1"
        assert tcp.auth_token is not None
    
    def test_tcp_endpoint(self):
        """Test TCP endpoint format."""
        tcp = TCPLocalhost(12345)
        endpoint = tcp.get_endpoint()
        assert endpoint == "tcp://127.0.0.1:12345"
    
    def test_tcp_roundtrip(self):
        """Test TCP message send/receive."""
        server = TCPLocalhost()
        received_messages = []
        
        def callback(msg):
            received_messages.append(msg)
        
        # Start server
        server.listen(callback)
        time.sleep(0.1)  # Give server time to start
        
        # Connect client
        client = TCPLocalhost(server.port)
        assert client.connect()
        
        # Send message
        test_msg = {"test": "hello", "value": 42}
        client.send(test_msg)
        
        # Wait for processing
        time.sleep(0.1)
        
        # Verify message received
        assert len(received_messages) == 1
        assert received_messages[0] == test_msg
        
        # Cleanup
        client.close()
        server.close()


@pytest.mark.skipif(sys.platform != "darwin" and sys.platform != "linux", 
                  reason="Unix domain sockets only on Unix-like systems")
class TestUnixDomainSocket:
    """Test Unix domain socket implementation."""
    
    def test_uds_creation(self):
        """Test UDS creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sock_path = os.path.join(tmpdir, "test.sock")
            uds = UnixDomainSocket(sock_path)
            assert uds.socket_path == sock_path
    
    def test_uds_endpoint(self):
        """Test UDS endpoint format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sock_path = os.path.join(tmpdir, "test.sock")
            uds = UnixDomainSocket(sock_path)
            endpoint = uds.get_endpoint()
            assert endpoint == sock_path
    
    def test_uds_roundtrip(self):
        """Test UDS message send/receive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sock_path = os.path.join(tmpdir, "test.sock")
            server = UnixDomainSocket(sock_path)
            received_messages = []
            
            def callback(msg):
                received_messages.append(msg)
            
            # Start server
            server.listen(callback)
            time.sleep(0.1)  # Give server time to start
            
            # Connect client
            client = UnixDomainSocket(sock_path)
            assert client.connect()
            
            # Send message
            test_msg = {"test": "hello", "value": 42}
            client.send(test_msg)
            
            # Wait for processing
            time.sleep(0.1)
            
            # Verify message received
            assert len(received_messages) == 1
            assert received_messages[0] == test_msg
            
            # Cleanup
            client.close()
            server.close()


@pytest.mark.skipif(not WINDOWS_PIPES_AVAILABLE, 
                  reason="Windows named pipes not available (pywin32 not installed)")
class TestWindowsNamedPipe:
    """Test Windows named pipe implementation."""
    
    def test_pipe_creation(self):
        """Test named pipe creation."""
        pipe_name = f"test_pipe_{uuid.uuid4().hex[:8]}"
        pipe = WindowsNamedPipe(pipe_name)
        assert pipe_name in pipe.get_endpoint()
        assert pipe.auth_token is not None
    
    def test_pipe_endpoint(self):
        """Test named pipe endpoint format."""
        pipe_name = "test_pipe"
        pipe = WindowsNamedPipe(pipe_name)
        endpoint = pipe.get_endpoint()
        assert endpoint == f"\\\\.\\pipe\\{pipe_name}"
    
    @pytest.mark.skipif(True, reason="Named pipe tests require admin privileges")
    def test_pipe_roundtrip(self):
        """Test named pipe message send/receive."""
        pytest.skip("Named pipe tests require special setup")


class TestIPCIntegration:
    """Test cross-platform IPC integration."""
    
    def test_get_ipc_transport_auto(self):
        """Test automatic IPC transport selection."""
        transport = get_ipc_transport("auto")
        
        if sys.platform == "win32":
            # Should prefer named pipes on Windows if available
            if WINDOWS_PIPES_AVAILABLE:
                assert "WindowsNamedPipe" in type(transport).__name__
            else:
                # Fall back to TCP
                assert "TCPLocalhost" in type(transport).__name__
        else:
            # Should use UDS on Unix-like systems
            assert "UnixDomainSocket" in type(transport).__name__
    
    def test_get_ipc_transport_explicit(self):
        """Test explicit IPC transport selection."""
        # Test TCP selection
        tcp = get_ipc_transport("tcp")
        assert "TCPLocalhost" in type(tcp).__name__
        
        # Test UDS selection (skip on Windows)
        if sys.platform != "win32":
            with tempfile.TemporaryDirectory() as tmpdir:
                sock_path = os.path.join(tmpdir, "test.sock")
                uds = get_ipc_transport("uds")
                # Override with our path for testing
                uds.socket_path = sock_path
                assert "UnixDomainSocket" in type(uds).__name__
        
        # Test named pipe selection (skip if not available)
        if WINDOWS_PIPES_AVAILABLE:
            pipe = get_ipc_transport("named_pipe")
            pipe_type = type(pipe).__name__
            assert "WindowsNamedPipe" in pipe_type


class TestMessageSerialization:
    """Test that message serialization works correctly."""
    
    def test_json_serialization(self):
        """Test JSON message handling."""
        test_messages = [
            {"simple": "message"},
            {"with_unicode": "hello 世界"},
            {"with_numbers": [1, 2, 3.14]},
            {"nested": {"a": {"b": "c"}}},
            {"with_null": None},
        ]
        
        for msg in test_messages:
            # Test that JSON serialization/deserialization works
            serialized = json.dumps(msg)
            deserialized = json.loads(serialized)
            assert deserialized == msg


if __name__ == "__main__":
    # Run tests when executed directly
    import pytest
    pytest.main([__file__, "-v"])
