#!/usr/bin/env python3
import os, sys, subprocess, requests, time
from datetime import datetime

RED = "[91m"
GREEN = "[92m"
CYAN = "[96m"
YELLOW = "[93m"
BOLD = "[1m"
NC = "[0m"

def get_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text.strip()
    except:
        return "Unknown"

def main():
    print(CYAN + BOLD + """
  ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
 ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
 ██║  ███╗███████║██║   ██║███████╗   ██║
 ██║   ██║██╔══██║██║   ██║╚════██║   ██║
 ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║
  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝
""" + NC)
    print(YELLOW + "  [ Invisible Mode — by Rehsijas ]" + NC + "\n")

    real_ip = get_ip()
    print(RED + "[-] Your real IP: " + real_ip + NC)

    print("\n" + CYAN + "[*] Checking VPN..." + NC)
    vpn = subprocess.run(["ifconfig"], capture_output=True, text=True)
    if "utun" in vpn.stdout or "tun0" in vpn.stdout:
        print(GREEN + "[+] VPN detected" + NC)
    else:
        print(YELLOW + "[!] No VPN — recommend ProtonVPN or Mullvad" + NC)

    print("\n" + CYAN + "[*] Checking Tor..." + NC)
    tor_check = subprocess.run(["which", "tor"], capture_output=True, text=True)
    if tor_check.returncode == 0:
        print(GREEN + "[+] Tor found — starting..." + NC)
        subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        print(GREEN + "[+] Tor running on port 9050" + NC)
    else:
        print(YELLOW + "[!] Tor not found — installing..." + NC)
        os.system("brew install tor 2>/dev/null")
        os.system("brew services start tor 2>/dev/null")
        print(GREEN + "[+] Tor installed" + NC)

    print("\n" + CYAN + "[*] Flushing DNS..." + NC)
    os.system("sudo dscacheutil -flushcache 2>/dev/null")
    os.system("sudo killall -HUP mDNSResponder 2>/dev/null")
    print(GREEN + "[+] DNS cache cleared" + NC)

    print("\n" + CYAN + "[*] Checking IP after setup..." + NC)
    time.sleep(2)
    new_ip = get_ip()
    if new_ip != real_ip:
        print(GREEN + "[+] IP changed: " + real_ip + " -> " + new_ip + NC)
        print("\n" + GREEN + BOLD + "[✓] GHOST MODE ACTIVE — You are hidden" + NC)
    else:
        print(YELLOW + "[!] IP unchanged: " + new_ip + NC)
        print(YELLOW + "[!] Enable a VPN for full anonymity" + NC)
        print("\n" + YELLOW + "[~] GHOST MODE PARTIAL — Enable VPN for full cover" + NC)

    print("\n" + CYAN + "  Now run: hack <target>" + NC + "\n")

if __name__ == "__main__":
    main()
