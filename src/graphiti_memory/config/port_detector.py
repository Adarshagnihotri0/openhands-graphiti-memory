"""Port detection utility for proxy auto-configuration."""

import os
from typing import Optional

import requests

from .settings import GraphitiConfig


class PortDetector:
    """Auto-detect proxy port from configuration."""

    @staticmethod
    def detect_port(config: Optional[GraphitiConfig] = None) -> Optional[int]:
        """
        Auto-detect which port the proxy is running on.
        
        Uses configuration from GraphitiConfig (environment variables).
        
        Args:
            config: Optional GraphitiConfig instance (creates default if None)
        
        Returns:
            Port number if found, None otherwise
        """
        if config is None:
            config = GraphitiConfig()
        
        ports = config.get_proxy_ports()
        timeout = config.proxy_timeout
        
        for port in ports:
            try:
                response = requests.get(
                    f"http://localhost:{port}/health",
                    timeout=timeout
                )
                if response.status_code == 200:
                    return port
            except requests.RequestException:
                continue
        
        return None
    
    @staticmethod
    def get_proxy_url(config: Optional[GraphitiConfig] = None) -> str:
        """
        Get proxy URL with auto-detection fallback.
        
        Priority order:
        1. llm_base_url from config (if set)
        2. BEDROCK_PROXY_URL env var
        3. Auto-detect from proxy_ports
        4. Default to first port in proxy_ports
        
        Args:
            config: Optional GraphitiConfig instance
        
        Returns:
            Proxy URL string
        """
        if config is None:
            config = GraphitiConfig()
        
        # If base_url already set, use it
        if config.llm_base_url:
            return config.llm_base_url
        
        # Check environment variable
        env_url = os.getenv("BEDROCK_PROXY_URL")
        if env_url:
            return env_url
        
        # Auto-detect
        detected_port = PortDetector.detect_port(config)
        if detected_port:
            return f"http://localhost:{detected_port}"
        
        # Fallback to first port
        default_port = config.get_proxy_ports()[0]
        return f"http://localhost:{default_port}"
    
    @staticmethod
    def is_port_running(port: int, timeout: int = 2) -> bool:
        """
        Check if a specific port is running.
        
        Args:
            port: Port number to check
            timeout: Timeout in seconds
        
        Returns:
            True if port is responding, False otherwise
        """
        try:
            response = requests.get(
                f"http://localhost:{port}/health",
                timeout=timeout
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
