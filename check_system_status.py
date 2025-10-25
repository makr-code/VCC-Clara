#!/usr/bin/env python3
"""
Clara AI System - Complete Status Check
========================================
Checks all components: Backends, Frontends, UDS3 Integration
"""

import requests
from colorama import init, Fore, Style
import sys

init(autoreset=True)

def check_backend(name: str, port: int, check_uds3: bool = False):
    """Check backend health"""
    try:
        response = requests.get(f"http://localhost:{port}/health", timeout=3)
        data = response.json()
        
        print(f"{Fore.GREEN}✅ {name}: HEALTHY{Style.RESET_ALL}")
        print(f"   Port: {port}")
        
        if "active_jobs" in data:
            print(f"   Active Jobs: {data['active_jobs']}")
        
        if check_uds3 and "uds3_available" in data:
            uds3_status = data['uds3_available']
            color = Fore.GREEN if uds3_status else Fore.YELLOW
            print(f"   UDS3: {color}{uds3_status}{Style.RESET_ALL}")
        
        if "datasets_count" in data:
            print(f"   Datasets: {data['datasets_count']}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ {name}: UNAVAILABLE{Style.RESET_ALL}")
        print(f"   Error: {str(e)[:50]}")
        return False

def main():
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  CLARA AI SYSTEM - STATUS CHECK")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Check Backends
    print(f"{Fore.YELLOW}BACKEND SERVICES:{Style.RESET_ALL}\n")
    
    training_ok = check_backend("Training Backend", 45680)
    print()
    dataset_ok = check_backend("Dataset Backend", 45681, check_uds3=True)
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  SUMMARY")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    total = 2
    running = sum([training_ok, dataset_ok])
    
    if running == total:
        print(f"{Fore.GREEN}✅ All systems operational ({running}/{total}){Style.RESET_ALL}")
        sys.exit(0)
    elif running > 0:
        print(f"{Fore.YELLOW}⚠️ Partial system running ({running}/{total}){Style.RESET_ALL}")
        sys.exit(1)
    else:
        print(f"{Fore.RED}❌ No services running{Style.RESET_ALL}")
        sys.exit(2)

if __name__ == "__main__":
    main()
