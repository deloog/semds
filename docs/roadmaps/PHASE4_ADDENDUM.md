# Phase 4 Roadmap Addendum

## New Section 4.6: Human Gate

To align with SEMDS_v1.1_SPEC.md Section 4.7, Phase 4 needs to add:

### Task List

| Task ID | Task | Est | Dep | Owner |
|---------|------|-----|-----|-------|
| P4-T25 | Implement HumanGateMonitor class | 4h | - | AI |
| P4-T26 | Implement review quality monitoring | 3h | P4-T25 | AI |
| P4-T27 | Implement approval API routes | 2h | P4-T25 | AI |
| P4-T28 | Implement approval dialog UI | 3h | P4-T27 | AI |
| P4-T29 | Human gate unit tests | 2h | P4-T25-P4-T28 | AI |

### Core Requirements

HumanGateMonitor must implement:

1. Review quality monitoring
   - Track consecutive approval rate (>98% triggers warning)
   - Track average review time (<5 seconds triggers warning)
   - Alert human when quality degradation detected

2. L2 decision gating
   - All structure-affecting changes require human approval
   - Track review duration and decision

3. API Endpoints (from SEMDS_v1.1_SPEC.md Section 7.3)
   - GET    /api/approvals/pending - List pending approvals
   - POST   /api/approvals/{id}/approve - Approve
   - POST   /api/approvals/{id}/reject - Reject with reason

### Files to Create

- factory/human_gate.py - Core monitor class
- api/routers/approvals.py - Approval API routes

### UI Components to Add

- Pending approvals list in monitor UI
- Approval dialog with code diff view
- Review quality warning banner
