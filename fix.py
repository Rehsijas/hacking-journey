#!/usr/bin/env python3
import os, sys, re
from datetime import datetime

RED = "[91m"
GREEN = "[92m"
CYAN = "[96m"
YELLOW = "[93m"
MAGENTA = "[95m"
BLUE = "[94m"
BOLD = "[1m"
NC = "[0m"

def banner(target):
    print(GREEN + BOLD + """
 ███████╗██╗██╗  ██╗
 ██╔════╝██║╚██╗██╔╝
 █████╗  ██║ ╚███╔╝
 ██╔══╝  ██║ ██╔██╗
 ██║     ██║██╔╝ ██╗
 ╚═╝     ╚═╝╚═╝  ╚═╝
""" + NC)
    print(YELLOW + "  Target : " + BOLD + target + NC)
    print(YELLOW + "  Time   : " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + NC)
    print(GREEN + "  by Rehsijas — responsible disclosure" + NC + "\n")

def find_latest_report(target):
    reports_dir = os.path.expanduser("~/ghost-reports")
    if not os.path.exists(reports_dir):
        return None
    safe = target.replace("/","_").replace(":","_").replace("@","_")
    matches = []
    for d in os.listdir(reports_dir):
        if safe in d and os.path.isdir(reports_dir + "/" + d):
            matches.append(reports_dir + "/" + d)
    if not matches:
        return None
    return sorted(matches)[-1]

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except:
        return ""

def fix_sqli(report_dir, fix_report):
    sqli = read_file(report_dir + "/sqli.txt")
    if "injectable" in sqli.lower() or "parameter" in sqli.lower() or "sqlmap" in sqli.lower():
        print(RED + "[!] SQL INJECTION DETECTED" + NC)
        fix = """
FIX: SQL Injection
==================
VULNERABILITY: User input is directly concatenated into SQL queries.

VULNERABLE CODE EXAMPLE:
  $query = "SELECT * FROM users WHERE id=" + $_GET['id'];

FIXED CODE (PHP - Prepared Statements):
  $stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
  $stmt->execute([$_GET['id']]);

FIXED CODE (Python):
  cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

FIXED CODE (Node.js):
  db.query("SELECT * FROM users WHERE id = ?", [userId])

ADDITIONAL MEASURES:
  - Use an ORM (SQLAlchemy, Eloquent, Sequelize)
  - Validate and sanitize ALL user inputs
  - Use least privilege database accounts
  - Enable WAF rules for SQL injection patterns
  - Never display raw database errors to users
"""
        print(GREEN + fix + NC)
        fix_report.append(("SQL Injection", "CRITICAL", fix))
    else:
        print(GREEN + "[✓] No SQL injection found" + NC)

def fix_xss(report_dir, fix_report):
    xss = read_file(report_dir + "/xss.txt")
    if "xss" in xss.lower() or "script" in xss.lower() or "dalfox" in xss.lower():
        print(RED + "[!] XSS VULNERABILITY DETECTED" + NC)
        fix = """
FIX: Cross-Site Scripting (XSS)
================================
VULNERABILITY: User input is reflected in HTML without sanitization.

VULNERABLE CODE EXAMPLE:
  echo "<p>Hello " + $_GET['name'] + "</p>";

FIXED CODE (PHP):
  echo "<p>Hello " + htmlspecialchars($_GET['name'], ENT_QUOTES, 'UTF-8') + "</p>";

FIXED CODE (JavaScript):
  element.textContent = userInput;  // NOT innerHTML

FIXED CODE (Python/Jinja2):
  {{ user_input | e }}  // auto-escaping enabled

SECURITY HEADERS TO ADD:
  Content-Security-Policy: default-src 'self'
  X-XSS-Protection: 1; mode=block
  X-Content-Type-Options: nosniff

ADDITIONAL MEASURES:
  - Use a templating engine with auto-escaping
  - Implement Content Security Policy (CSP)
  - Validate input on both client and server side
  - Use DOMPurify for sanitizing HTML content
"""
        print(GREEN + fix + NC)
        fix_report.append(("XSS", "HIGH", fix))
    else:
        print(GREEN + "[✓] No XSS found" + NC)

def fix_headers(report_dir, fix_report):
    headers = read_file(report_dir + "/headers.txt")
    missing = []
    checks = {
        "X-Frame-Options": "Prevents clickjacking",
        "X-Content-Type-Options": "Prevents MIME sniffing",
        "Content-Security-Policy": "Prevents XSS and injection",
        "Strict-Transport-Security": "Forces HTTPS",
        "X-XSS-Protection": "Browser XSS filter",
        "Referrer-Policy": "Controls referrer information",
    }
    for header, desc in checks.items():
        if header.lower() not in headers.lower():
            missing.append((header, desc))

    if missing:
        print(RED + "[!] MISSING SECURITY HEADERS:" + NC)
        fix = "\nFIX: Missing Security Headers\n" + "="*35 + "\n\n"
        fix += "Add these headers to your web server:\n\n"
        fix += "Apache (.htaccess or httpd.conf):\n"
        for h, d in missing:
            print(YELLOW + "  [-] " + h + " — " + d + NC)
            fix += "  Header always set " + h + "\n"
        fix += """
Nginx (nginx.conf):
  add_header X-Frame-Options "SAMEORIGIN";
  add_header X-Content-Type-Options "nosniff";
  add_header X-XSS-Protection "1; mode=block";
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
  add_header Content-Security-Policy "default-src 'self'";
  add_header Referrer-Policy "strict-origin-when-cross-origin";

PHP (add to every page or bootstrap file):
  header("X-Frame-Options: SAMEORIGIN");
  header("X-Content-Type-Options: nosniff");
  header("X-XSS-Protection: 1; mode=block");
"""
        print(GREEN + fix + NC)
        fix_report.append(("Missing Headers", "MEDIUM", fix))
    else:
        print(GREEN + "[✓] Security headers look good" + NC)

def fix_ports(report_dir, fix_report):
    ports = read_file(report_dir + "/ports.txt")
    dangerous = {
        "21/tcp": ("FTP", "Use SFTP instead. FTP sends credentials in plaintext."),
        "23/tcp": ("Telnet", "Use SSH instead. Telnet is completely unencrypted."),
        "3306/tcp": ("MySQL", "Never expose database ports publicly. Bind to localhost only."),
        "5432/tcp": ("PostgreSQL", "Never expose database ports publicly. Bind to localhost only."),
        "27017/tcp": ("MongoDB", "MongoDB should never be publicly accessible."),
        "6379/tcp": ("Redis", "Redis has no auth by default. Bind to localhost only."),
        "445/tcp": ("SMB", "SMB should not be exposed to the internet."),
        "3389/tcp": ("RDP", "RDP is heavily targeted. Use VPN + restrict access."),
    }
    found_dangerous = []
    for port, (service, advice) in dangerous.items():
        if port in ports:
            found_dangerous.append((port, service, advice))

    if found_dangerous:
        print(RED + "[!] DANGEROUS OPEN PORTS:" + NC)
        fix = "\nFIX: Dangerous Open Ports\n" + "="*30 + "\n\n"
        for port, service, advice in found_dangerous:
            print(YELLOW + "  [-] " + port + " (" + service + ") — " + advice + NC)
            fix += port + " (" + service + "):\n  " + advice + "\n\n"
        fix += """
FIREWALL RULES (Linux/iptables):
  iptables -A INPUT -p tcp --dport 3306 -j DROP
  iptables -A INPUT -p tcp --dport 6379 -j DROP

macOS Firewall:
  System Settings -> Network -> Firewall -> enable and configure

GENERAL RULE:
  Close every port you dont need. Open only what you must.
"""
        print(GREEN + fix + NC)
        fix_report.append(("Dangerous Ports", "HIGH", fix))
    else:
        print(GREEN + "[✓] No dangerous ports exposed" + NC)

def fix_ssl(report_dir, fix_report):
    ssl = read_file(report_dir + "/ssl.txt")
    if "error" in ssl.lower() or not ssl.strip():
        print(YELLOW + "[!] SSL/TLS issues detected" + NC)
        fix = """
FIX: SSL/TLS Configuration
============================
ISSUES: Weak SSL config, missing HTTPS, or expired cert.

FREE SSL CERTIFICATE:
  certbot --apache -d yourdomain.com
  certbot --nginx -d yourdomain.com
  (Let's Encrypt - free, auto-renews)

STRONG TLS CONFIG (nginx):
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
  ssl_prefer_server_ciphers off;
  ssl_session_cache shared:SSL:10m;

FORCE HTTPS (Apache):
  RewriteEngine On
  RewriteCond %{HTTPS} off
  RewriteRule ^(.*)$ https://%\{HTTP_HOST\}%\{REQUEST_URI\} [L,R=301]

TEST YOUR SSL:
  https://ssllabs.com/ssltest/
"""
        print(GREEN + fix + NC)
        fix_report.append(("SSL/TLS", "MEDIUM", fix))
    else:
        print(GREEN + "[✓] SSL looks okay" + NC)

def save_report(target, fix_report, report_dir):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path = report_dir + "/FIX_REPORT.txt"
    with open(path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("  FIX REPORT — by Rehsijas\n")
        f.write("  Target  : " + target + "\n")
        f.write("  Date    : " + timestamp + "\n")
        f.write("=" * 60 + "\n\n")
        if not fix_report:
            f.write("No vulnerabilities found.\n")
        else:
            f.write("VULNERABILITIES FOUND: " + str(len(fix_report)) + "\n\n")
            for i, (vuln, severity, fix) in enumerate(fix_report, 1):
                f.write(str(i) + ". [" + severity + "] " + vuln + "\n")
                f.write("-" * 40 + "\n")
                f.write(fix + "\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write("Report generated by ghost toolkit — Rehsijas\n")
        f.write("For bug bounty: attach this file to your report\n")
        f.write("=" * 60 + "\n")
    return path

def main():
    if len(sys.argv) < 2:
        print(RED + "Usage: fix <target>" + NC)
        print(YELLOW + "  fix target.com" + NC)
        print(YELLOW + "  fix localhost" + NC)
        sys.exit(1)

    target = sys.argv[1]
    banner(target)

    report_dir = find_latest_report(target)
    if not report_dir:
        print(RED + "[!] No hack/attack report found for: " + target + NC)
        print(YELLOW + "[!] Run: hack " + target + " first" + NC)
        sys.exit(1)

    print(CYAN + "[+] Reading report: " + report_dir + NC + "\n")
    print(MAGENTA + BOLD + "=== ANALYZING VULNERABILITIES ===" + NC + "\n")

    fix_report = []
    fix_sqli(report_dir, fix_report)
    fix_xss(report_dir, fix_report)
    fix_headers(report_dir, fix_report)
    fix_ports(report_dir, fix_report)
    fix_ssl(report_dir, fix_report)

    print("\n" + MAGENTA + BOLD + "=== GENERATING FIX REPORT ===" + NC)
    report_path = save_report(target, fix_report, report_dir)

    print("\n" + GREEN + BOLD + "[✓] FIX COMPLETE" + NC)
    print(CYAN + "[+] Vulnerabilities found : " + str(len(fix_report)) + NC)
    print(CYAN + "[+] Fix report saved      : " + report_path + NC)
    print(CYAN + "[+] Attach to bug bounty  : " + report_path + NC)

    if fix_report:
        print("\n" + YELLOW + "Summary:" + NC)
        for vuln, severity, _ in fix_report:
            color = RED if severity == "CRITICAL" else YELLOW if severity == "HIGH" else BLUE
            print("  " + color + "[" + severity + "]" + NC + " " + vuln)
    print()

if __name__ == "__main__":
    main()
