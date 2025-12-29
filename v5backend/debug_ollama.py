#!/usr/bin/env python3
"""
Debug script to check Ollama configuration and connectivity
"""
import os
import sys
import subprocess
import time
import requests

def check_environment():
    """Check relevant environment variables"""
    print("🔍 Environment Variables:")
    env_vars = [
        'OLLAMA_HOST', 'OLLAMA_ORIGINS', 'OLLAMA_HOST_BIND',
        'OLLAMA_KEEP_ALIVE', 'OLLAMA_NUM_PARALLEL', 'OLLAMA_MAX_LOADED_MODELS'
    ]
    
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        print(f"   {var}: {value}")

def check_ollama_process():
    """Check if Ollama process is running"""
    print("\n🔍 Ollama Process Status:")
    try:
        result = subprocess.run(['pgrep', '-f', 'ollama'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"   ✅ Ollama processes found: {', '.join(pids)}")
            
            # Check process details
            for pid in pids:
                try:
                    cmd_result = subprocess.run(['ps', '-p', pid, '-o', 'pid,cmd'], 
                                              capture_output=True, text=True)
                    if cmd_result.returncode == 0:
                        print(f"   📋 PID {pid}: {cmd_result.stdout.split('\n')[1]}")
                except:
                    pass
        else:
            print("   ❌ No Ollama processes found")
    except Exception as e:
        print(f"   ⚠️  Error checking processes: {e}")

def check_network_binding():
    """Check what ports are being listened on"""
    print("\n🌐 Network Listening Ports:")
    try:
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if '11434' in line or 'ollama' in line.lower():
                    print(f"   📡 {line.strip()}")
        else:
            print("   ⚠️  netstat not available, trying ss...")
            result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if '11434' in line:
                        print(f"   📡 {line.strip()}")
    except Exception as e:
        print(f"   ⚠️  Error checking network: {e}")

def test_ollama_connectivity():
    """Test connectivity to Ollama API"""
    print("\n🔗 Ollama API Connectivity:")
    
    hosts_to_test = [
        'http://127.0.0.1:11434',
        'http://localhost:11434',
        os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')
    ]
    
    for host in set(hosts_to_test):  # Remove duplicates
        print(f"\n   Testing: {host}")
        try:
            response = requests.get(f"{host}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {host} - Connected successfully")
                data = response.json()
                models = data.get('models', [])
                print(f"   📦 Models available: {len(models)}")
                for model in models[:3]:  # Show first 3 models
                    print(f"      - {model.get('name', 'Unknown')}")
            else:
                print(f"   ⚠️  {host} - HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ {host} - Connection refused")
        except requests.exceptions.Timeout:
            print(f"   ⏰ {host} - Timeout")
        except Exception as e:
            print(f"   ❌ {host} - Error: {e}")

def check_dns_resolution():
    """Check DNS resolution for problematic hostnames"""
    print("\n🌐 DNS Resolution Check:")
    
    hostnames = [
        'ollama.railway.internal',
        'localhost',
        '127.0.0.1'
    ]
    
    for hostname in hostnames:
        try:
            import socket
            if hostname == '127.0.0.1':
                print(f"   ✅ {hostname} - IP address (no DNS needed)")
                continue
                
            result = socket.gethostbyname(hostname)
            print(f"   ✅ {hostname} -> {result}")
        except socket.gaierror as e:
            print(f"   ❌ {hostname} - DNS resolution failed: {e}")
        except Exception as e:
            print(f"   ⚠️  {hostname} - Error: {e}")

def main():
    print("🚂 Railway Ollama Debug Tool")
    print("=" * 50)
    
    check_environment()
    check_ollama_process()
    check_network_binding()
    test_ollama_connectivity()
    check_dns_resolution()
    
    print("\n" + "=" * 50)
    print("🔧 Recommendations:")
    
    ollama_host = os.environ.get('OLLAMA_HOST', 'NOT SET')
    if 'railway.internal' in ollama_host:
        print("   ⚠️  OLLAMA_HOST contains 'railway.internal' - this should be localhost/127.0.0.1")
    
    if ollama_host == 'NOT SET':
        print("   ⚠️  OLLAMA_HOST not set - should be http://127.0.0.1:11434")
    
    print("   💡 For Railway deployment, use: OLLAMA_HOST=http://127.0.0.1:11434")
    print("   💡 Ensure Ollama serves on 127.0.0.1:11434, not external interfaces")

if __name__ == "__main__":
    main()
