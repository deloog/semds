# Phase 3 Roadmap Addendum

## New Section 3.3b: Skills Library (Layer 1)

To align with SEMDS_v1.1_SPEC.md Section 3.1 and Chapter 5, Phase 3 needs to add the Skills Library layer:

### Task List

| Task ID | Task | Est | Dep | Owner |
|---------|------|-----|-----|-------|
| P3-T18a | Create skills/ directory structure | 1h | - | AI |
| P3-T18b | Implement code generation templates (Jinja2) | 3h | P3-T18a | AI |
| P3-T18c | Implement strategy registry | 2h | P3-T18a | AI |
| P3-T18d | Implement verified strategy入库logic | 2h | P3-T18c | AI |
| P3-T18e | Skills library unit tests | 2h | P3-T18b-P3-T18d | AI |

### Directory Structure

```
skills/
├── templates/
│   ├── python_function.j2
│   └── class_implementation.j2
└── strategies/
    └── strategy_registry.json
```

### Files to Create

1. skills/template_manager.py - Template rendering
2. skills/strategy_registry.py - Strategy registry management

### Dual Evaluator Update (P3-T10a)

Add new task:
| P3-T10a | Implement AI-generated edge cases | 3h | P3-T7 | AI |

The _generate_edge_cases method must use Claude API to generate boundary test cases,
not use hardcoded values. This is critical for Goodhart detection.

See SEMDS_v1.1_SPEC.md Section 9.2 for EDGE_CASE_GENERATION_PROMPT template.
