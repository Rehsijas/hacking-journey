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
 ██╗  ██╗ █████╗  ██████╗██╗  ██╗
 ██║  ██║██╔══██╗██╔════╝██║ ██╔╝
 ███████║███████║██║     █████╔╝
 ██╔══██║██╔══██║██║     ██╔═██╗
 ██║  ██║██║  ██║╚██████╗██║  ██╗
 ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
""" + NC)
    print(YELLOW + "  Target : " + BOLD + target + NC)
    print(YELLOW + "  Time   : " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + NC)
    print(RED + "  by Rehsijas" + NC + "\n")

def detect_type(target):
    if re.match(r"^\+?[\d\s\-]{7,15}$", target): return "phone"
    if re.match(r"^[\w\.\-]+@[\w\.\-]+\.\w+$", target): return "email"
    if target.startswith("@"): return "username"
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", target): return "ip"
    if target.startswith(chr(34)) and target.endswith(chr(34)): return "company"
    return "domain"

def make_report_dir(target):
    safe = target.replace("/","_").replace(":","_").replace("@","_").replace(" ","_")
    path = os.path.expanduser("~/ghost-reports/" + safe + "_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(path, exist_ok=True)
    return path

def run_cmd(cmd, label, report_dir, filename, timeout=120):
    print("\n" + CYAN + "[*] " + label + "..." + NC)
    out_file = report_dir + "/" + filename + ".txt"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        output = result.stdout + result.stderr
        with open(out_file, "w") as f:
            f.write(output)
        if output.strip():
            print(GREEN + output[:600] + NC)
            if len(output) > 600:
                print(YELLOW + "  [+] Full output -> " + out_file + NC)
        else:
            print(YELLOW + "  [!] No output" + NC)
        return output
    except subprocess.TimeoutExpired:
        print(YELLOW + "  [!] Timed out — moving on" + NC)
        return ""

def hack_domain(target, rd):
    print("\n" + MAGENTA + BOLD + "=== DOMAIN RECON ===" + NC)
    run_cmd("whois " + target + " 2>/dev/null | head -40", "WHOIS lookup", rd, "whois")
    run_cmd("dig ANY " + target + " +noall +answer 2>/dev/null", "DNS records", rd, "dns")
    run_cmd("subfinder -d " + target + " -silent 2>/dev/null", "Subdomains", rd, "subdomains")
    run_cmd("curl -sk https://" + target + " -I 2>/dev/null | head -20", "HTTP headers", rd, "headers")
    run_cmd("theHarvester -d " + target + " -b google,bing -l 100 2>/dev/null | tail -50", "Email harvest", rd, "emails")
    run_cmd("sudo nmap -sV -sC --open -T4 " + target + " 2>/dev/null", "Port scan", rd, "ports")
    run_cmd("nuclei -u " + target + " -severity low,medium,high,critical -silent 2>/dev/null | head -30", "Vuln scan", rd, "vulns")
    run_cmd("curl -sk https://crt.sh/?q=" + target + "&output=json 2>/dev/null | python3 -c \"import sys,json;[print(d[chr(110)+chr(97)+chr(109)+chr(101)+chr(95)+chr(118)+chr(97)+chr(108)+chr(117)+chr(101)]) for d in json.load(sys.stdin)[:20]]\" 2>/dev/null", "SSL cert recon", rd, "ssl")

def hack_ip(target, rd):
    print("\n" + MAGENTA + BOLD + "=== IP RECON ===" + NC)
    run_cmd("whois " + target + " 2>/dev/null | head -30", "WHOIS", rd, "whois")
    run_cmd("dig -x " + target + " +short 2>/dev/null", "Reverse DNS", rd, "rdns")
    run_cmd("curl -sk https://ipapi.co/" + target + "/json/ 2>/dev/null", "Geolocation", rd, "geo")
    run_cmd("sudo nmap -sV -sC -O --open -T4 " + target + " 2>/dev/null", "Deep port scan", rd, "ports")
    run_cmd("nuclei -u " + target + " -severity medium,high,critical -silent 2>/dev/null | head -20", "Vuln scan", rd, "vulns")

def hack_username(target, rd):
    u = target.lstrip("@")
    print("\n" + MAGENTA + BOLD + "=== USERNAME RECON ===" + NC)
    run_cmd("sherlock " + u + " 2>/dev/null", "Sherlock (300+ platforms)", rd, "sherlock", timeout=180)
    run_cmd("python3 -m maigret " + u + " --timeout 10 2>/dev/null | tail -30", "Maigret deep profile", rd, "maigret", timeout=180)

def hack_phone(target, rd):
    print("\n" + MAGENTA + BOLD + "=== PHONE RECON ===" + NC)
    run_cmd("phoneinfoga scan -n " + chr(39) + target + chr(39) + " 2>/dev/null", "PhoneInfoga", rd, "phone")

def hack_email(target, rd):
    print("\n" + MAGENTA + BOLD + "=== EMAIL RECON ===" + NC)
    domain = target.split("@")[1]
    run_cmd("theHarvester -d " + domain + " -b google,bing -l 50 2>/dev/null | tail -30", "Domain harvest", rd, "harvest")
    run_cmd("dig MX " + domain + " +short 2>/dev/null", "MX records", rd, "mx")

def hack_company(target, rd):
    company = target.strip(chr(34))
    print("\n" + MAGENTA + BOLD + "=== COMPANY RECON ===" + NC)
    run_cmd("theHarvester -d " + chr(39) + company + chr(39) + " -b google,bing,linkedin -l 200 2>/dev/null | tail -50", "Company harvest", rd, "harvest")

def main():
    if len(sys.argv) < 2:
        print(RED + "Usage: hack <target>" + NC)
        print(YELLOW + "Examples:" + NC)
        print("  hack target.com")
        print("  hack 192.168.1.1")
        print("  hack @username")
        print("  hack +4915123456789")
        print("  hack user@email.com")
        sys.exit(1)
    target = " ".join(sys.argv[1:])
    t = detect_type(target)
    rd = make_report_dir(target)
    banner(target)
    print(GREEN + "[+] Type detected: " + BOLD + t.upper() + NC)
    print(GREEN + "[+] Saving to: " + rd + NC)
    if t == "domain": hack_domain(target, rd)
    elif t == "ip": hack_ip(target, rd)
    elif t == "username": hack_username(target, rd)
    elif t == "phone": hack_phone(target, rd)
    elif t == "email": hack_email(target, rd)
    elif t == "company": hack_company(target, rd)
    print("\n" + GREEN + BOLD + "[✓] HACK COMPLETE" + NC)
    print(CYAN + "[+] Report: " + rd + NC)
    print(CYAN + "[+] Next: attack " + target + NC + "\n")

if __name__ == "__main__":
    main()
