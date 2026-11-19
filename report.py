"""Writes REPORT.md: every finding in findings.toml, fixed or open, from its regression test."""
import subprocess
import sys
import tomllib

with open("findings.toml", "rb") as f:
    review = tomllib.load(f)

rows, fixed = [], 0
for finding in review["finding"]:
    test = subprocess.run([sys.executable, "-m", "pytest", "-q", finding["test"]], capture_output=True)
    status = "fixed" if test.returncode == 0 else "open"
    fixed += status == "fixed"
    rows.append(f"| {finding['id']} | {finding['title']} | {finding['severity']} | {status} "
                f"| {finding['found_by']} |")

total = len(rows)
summary = f"{total} findings: {fixed} fixed, {total - fixed} open."
with open("REPORT.md", "w") as f:
    f.write("# Security report: help desk\n\n")
    f.write(f"Scope: {review['scope']}.\n\n")
    f.write("| ID | Finding | Severity | Status | Found by |\n|---|---|---|---|---|\n")
    f.write("\n".join(rows) + "\n\n")
    f.write(f"{summary}\nEach status comes from the finding's regression test.\n")
print(f"Wrote REPORT.md. {summary}")
