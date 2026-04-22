# 🧪 TESTER Skill - Test Execution & Validation

## Skill Definition

**Name:** `/gsd-test-execution`  
**Agent:** TESTER  
**Purpose:** Execute test suite and generate technical feedback for TESTED sprints

---

## Trigger Conditions

1. Sprint status = `TESTED` in `docs/BACKLOG.md`
2. Walkthrough exists in `docs/walkthrough/done/walkthrough-{sprint-id}.md`
3. Auto-monitor active OR manual invocation

---

## Execution Flow

### Step 1: Detect TESTED Sprint

```python
def detect_tested_sprint():
    """Read BACKLOG.md and find sprints with TESTED status."""
    backlog = read_file("docs/BACKLOG.md")
    
    # Parse Active Sprint Queue section
    active_sprints = parse_active_sprints(backlog)
    
    # Filter TESTED sprints
    tested_sprints = [s for s in active_sprints if s.status == "TESTED"]
    
    return tested_sprints
```

### Step 2: Verify Walkthrough

```python
def verify_walkthrough(sprint_id):
    """Check if walkthrough exists for sprint."""
    walkthrough_path = f"docs/walkthrough/done/walkthrough-{sprint_id}.md"
    
    if not file_exists(walkthrough_path):
        log_warning(f"Sprint {sprint_id} is TESTED but walkthrough missing")
        return False
    
    return True
```

### Step 3: Execute Test Suite

```bash
# Run pytest with quiet mode and short traceback
python -m pytest tests/ -q --tb=short

# Capture output:
# - Total tests
# - Passed count
# - Failed count
# - Skipped count
# - Duration
```

### Step 4: Execute Quality Check

```bash
# Run ruff linter
python -m ruff check gedai/ tests/

# Capture output:
# - Violations count
# - Violation details (if any)
```

### Step 5: Load Baseline Metrics

```python
def load_baseline():
    """Load metrics from previous technical feedback."""
    # Find latest technical-feedback file
    feedback_files = list_files("docs/technical-feedback/")
    latest = sorted(feedback_files)[-1]
    
    # Parse metrics
    baseline = parse_feedback_metrics(latest)
    
    return {
        "tests_passing": baseline.tests_passing,
        "test_coverage": baseline.test_coverage,
        "execution_time": baseline.execution_time,
        "ruff_violations": baseline.ruff_violations
    }
```

### Step 6: Analyze Results

```python
def analyze_results(current, baseline):
    """Compare current results with baseline."""
    analysis = {
        "regressions": [],
        "improvements": [],
        "status": "PASS"
    }
    
    # Check test pass rate
    if current.tests_passing < baseline.tests_passing:
        analysis["regressions"].append({
            "metric": "Tests Passing",
            "baseline": baseline.tests_passing,
            "current": current.tests_passing,
            "delta": current.tests_passing - baseline.tests_passing
        })
        analysis["status"] = "FAIL"
    
    # Check ruff violations
    if current.ruff_violations > 0:
        analysis["regressions"].append({
            "metric": "Ruff Violations",
            "baseline": 0,
            "current": current.ruff_violations,
            "delta": current.ruff_violations
        })
        analysis["status"] = "FAIL"
    
    # Check execution time degradation (>20% slower)
    time_delta_pct = ((current.execution_time - baseline.execution_time) / baseline.execution_time) * 100
    if time_delta_pct > 20:
        analysis["regressions"].append({
            "metric": "Execution Time",
            "baseline": baseline.execution_time,
            "current": current.execution_time,
            "delta_pct": time_delta_pct
        })
        # WARNING only, not FAIL
    
    return analysis
```

### Step 7: Generate Technical Feedback

```python
def generate_technical_feedback(sprint, results, analysis):
    """Generate technical feedback markdown file."""
    
    # Determine version number
    today = datetime.now().strftime("%Y-%m-%d")
    existing = list_files(f"docs/technical-feedback/technical-feedback-{today}-v*.md")
    version = len(existing) + 1
    
    filename = f"docs/technical-feedback/technical-feedback-{today}-v{version}.md"
    
    # Build content
    content = f"""# Technical Feedback - {sprint.name}
**Date:** {today}  
**Tester:** TESTER Agent  
**Sprint Status:** TESTED → {"APPROVED" if analysis.status == "PASS" else "REJECTED"}

---

## Executive Summary

Sprint **{sprint.name}** has been tested and validated.

**Test Results:** {results.tests_passing}/{results.tests_total} passing ({results.pass_rate:.1f}%)  
**Code Quality:** {results.ruff_violations} violations  
**Execution Time:** {results.execution_time:.2f}s  
**Decision:** {"✅ APPROVED" if analysis.status == "PASS" else "❌ REJECTED"}

---

## Test Execution Results

### Full Suite
- **Total Tests:** {results.tests_total}
- **Passed:** {results.tests_passing} ({results.pass_rate:.1f}%)
- **Failed:** {results.tests_failed}
- **Skipped:** {results.tests_skipped}
- **Duration:** {results.execution_time:.2f}s

### Code Quality
- **Ruff Check:** {"PASS" if results.ruff_violations == 0 else "FAIL"}
- **Violations:** {results.ruff_violations}

---

## Regression Analysis

**Baseline:** {analysis.baseline_source}

| Metric | Baseline | Current | Delta | Status |
|--------|----------|---------|-------|--------|
"""
    
    # Add regression table rows
    for reg in analysis.regressions:
        status_icon = "❌" if reg.get("critical") else "⚠️"
        content += f"| {reg['metric']} | {reg['baseline']} | {reg['current']} | {reg['delta']} | {status_icon} |\n"
    
    for imp in analysis.improvements:
        content += f"| {imp['metric']} | {imp['baseline']} | {imp['current']} | {imp['delta']} | ✅ |\n"
    
    content += f"""
---

## Issues Found

### Critical (Blockers)
"""
    
    if analysis.status == "FAIL":
        for reg in analysis.regressions:
            if reg.get("critical"):
                content += f"- [ ] {reg['metric']}: {reg['description']}\n"
    else:
        content += "None\n"
    
    content += f"""
---

## Recommendations

"""
    
    if analysis.status == "PASS":
        content += "Sprint is ready for QA approval and DONE transition.\n"
    else:
        content += "Fix critical issues before requesting QA approval:\n"
        for i, reg in enumerate([r for r in analysis.regressions if r.get("critical")], 1):
            content += f"{i}. {reg['recommendation']}\n"
    
    content += f"""
---

## Approval Decision

**Status:** {"✅ APPROVED" if analysis.status == "PASS" else "❌ REJECTED"}

**Rationale:** {analysis.rationale}

**Next Steps:**
"""
    
    if analysis.status == "PASS":
        content += "- QA review and approve for DONE\n"
        content += "- Update BACKLOG.md to move sprint to Completed Archive\n"
    else:
        content += "- Fix critical issues listed above\n"
        content += "- Re-run test suite\n"
        content += "- Request TESTER re-validation\n"
    
    content += f"""
---

**Signed:** TESTER Agent  
**Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    # Write file
    write_file(filename, content)
    
    return filename
```

### Step 8: Notify QA

```python
def notify_qa(sprint, feedback_file, status):
    """Notify QA that sprint is ready for review."""
    
    message = f"""
🧪 TESTER Notification

Sprint: {sprint.name}
Status: {status}
Feedback: {feedback_file}

{"✅ Ready for QA approval" if status == "APPROVED" else "❌ Issues found - requires fixes"}
"""
    
    # Log notification
    log_info(message)
    
    # Optional: Send to notification system
    # send_notification(channel="qa", message=message)
```

---

## Auto-Monitor Implementation

### Schedule Function

```python
import time
import threading

class TesterMonitor:
    def __init__(self):
        self.active = True  # Default: ACTIVE
        self.interval = 600  # 10 minutes in seconds
        self.thread = None
    
    def start(self):
        """Start auto-monitor."""
        if self.thread and self.thread.is_alive():
            log_warning("Monitor already running")
            return
        
        self.active = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        log_info("TESTER monitor started (interval: 10 minutes)")
    
    def stop(self):
        """Stop auto-monitor."""
        self.active = False
        if self.thread:
            self.thread.join(timeout=5)
        log_info("TESTER monitor stopped")
    
    def status(self):
        """Get monitor status."""
        return {
            "active": self.active,
            "interval": self.interval,
            "running": self.thread and self.thread.is_alive()
        }
    
    def _monitor_loop(self):
        """Main monitor loop."""
        while self.active:
            try:
                # Check for TESTED sprints
                tested_sprints = detect_tested_sprint()
                
                for sprint in tested_sprints:
                    if verify_walkthrough(sprint.id):
                        log_info(f"Detected TESTED sprint: {sprint.name}")
                        
                        # Execute test suite
                        results = execute_test_suite()
                        
                        # Analyze results
                        baseline = load_baseline()
                        analysis = analyze_results(results, baseline)
                        
                        # Generate feedback
                        feedback_file = generate_technical_feedback(sprint, results, analysis)
                        
                        # Notify QA
                        notify_qa(sprint, feedback_file, analysis.status)
                
            except Exception as e:
                log_error(f"Monitor error: {e}")
            
            # Sleep for interval
            time.sleep(self.interval)

# Global monitor instance
_monitor = TesterMonitor()

def schedule_tester(action="status"):
    """Control TESTER auto-monitor."""
    if action == "on":
        _monitor.start()
        return "✅ TESTER monitor activated"
    elif action == "off":
        _monitor.stop()
        return "⏸️ TESTER monitor deactivated"
    elif action == "status":
        status = _monitor.status()
        return f"Monitor: {'🟢 ACTIVE' if status['active'] else '🔴 INACTIVE'} | Interval: {status['interval']}s"
    else:
        return "❌ Invalid action. Use: on, off, or status"
```

---

## Skill Commands

### `/gsd-test-execution`

Execute full test validation for TESTED sprints.

**Usage:**
```
/gsd-test-execution
```

**Output:**
- Technical feedback file created
- Console summary displayed
- QA notified

---

### `/schedule-tester [on|off|status]`

Control auto-monitor.

**Usage:**
```
/schedule-tester on      # Activate monitor
/schedule-tester off     # Deactivate monitor
/schedule-tester status  # Check status
```

**Default:** ACTIVE (starts automatically)

---

### `/tester-run [sprint-id]`

Manual test execution for specific sprint.

**Usage:**
```
/tester-run i-b          # Test sprint I-B
/tester-run              # Test all TESTED sprints
```

---

## Integration Example

### Scenario: Sprint I-B completed

```
1. Worker completes implementation
2. Worker creates walkthrough-i-b.md in docs/walkthrough/done/
3. Worker updates BACKLOG.md: Sprint I-B → TESTED
4. TESTER monitor detects change (within 10 minutes)
5. TESTER executes test suite
6. TESTER generates technical-feedback-2026-04-18-v1.md
7. TESTER notifies QA
8. QA reviews feedback
9. QA approves and moves sprint to DONE
```

---

## Quality Gates Enforcement

```python
def enforce_quality_gates(results):
    """Check if results meet quality gates."""
    gates = {
        "test_pass_rate": {"threshold": 95, "critical": True},
        "ruff_violations": {"threshold": 0, "critical": True},
        "test_coverage": {"threshold": 80, "critical": False},
        "execution_time": {"threshold": 10, "critical": False}
    }
    
    violations = []
    
    # Test pass rate
    if results.pass_rate < gates["test_pass_rate"]["threshold"]:
        violations.append({
            "gate": "Test Pass Rate",
            "threshold": f"≥{gates['test_pass_rate']['threshold']}%",
            "actual": f"{results.pass_rate:.1f}%",
            "critical": gates["test_pass_rate"]["critical"]
        })
    
    # Ruff violations
    if results.ruff_violations > gates["ruff_violations"]["threshold"]:
        violations.append({
            "gate": "Ruff Violations",
            "threshold": gates["ruff_violations"]["threshold"],
            "actual": results.ruff_violations,
            "critical": gates["ruff_violations"]["critical"]
        })
    
    # Test coverage (if available)
    if hasattr(results, "coverage") and results.coverage < gates["test_coverage"]["threshold"]:
        violations.append({
            "gate": "Test Coverage",
            "threshold": f"≥{gates['test_coverage']['threshold']}%",
            "actual": f"{results.coverage:.1f}%",
            "critical": gates["test_coverage"]["critical"]
        })
    
    # Execution time
    if results.execution_time > gates["execution_time"]["threshold"]:
        violations.append({
            "gate": "Execution Time",
            "threshold": f"<{gates['execution_time']['threshold']}s",
            "actual": f"{results.execution_time:.2f}s",
            "critical": gates["execution_time"]["critical"]
        })
    
    # Determine overall status
    critical_violations = [v for v in violations if v["critical"]]
    status = "FAIL" if critical_violations else ("WARNING" if violations else "PASS")
    
    return {
        "status": status,
        "violations": violations,
        "critical_count": len(critical_violations)
    }
```

---

**Version:** 1.0  
**Last Updated:** 2026-04-18  
**Maintained by:** TESTER Agent
