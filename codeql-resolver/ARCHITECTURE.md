# codeql-resolver — Architecture

Cross-plugin integration view for CodeQL alert resolution. For internal architecture
(command, agents, skills), see [README.md](README.md).

## Integration with the Ship Pipeline

```mermaid
flowchart TD
    classDef ai fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef external fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c
    classDef hook fill:#fff3e0,stroke:#e65100,color:#bf360c

    FPR["/finalize-pr\n(github-workflows)"]:::external
    RCQ["/resolve-codeql\n(this plugin)"]:::ai

    subgraph INTERNAL ["codeql-resolver internals"]
        direction TB
        CMD["/resolve-codeql command\nDiscover + classify alerts"]:::ai
        PA["Permissions Auditor\nagent"]:::ai
        EIF["Expression Injection Fixer\nagent"]:::ai
        GR["Generic Resolver\nagent"]:::ai
        SK1["Permission Classification\nskill"]:::ai
        SK2["Workflow Security Patterns\nskill"]:::ai

        CMD -->|"permissions alerts"| PA
        CMD -->|"injection alerts"| EIF
        CMD -->|"other alerts"| GR
        PA -.->|"uses"| SK1
        PA -.->|"uses"| SK2
        EIF -.->|"uses"| SK2
    end

    FPR -->|"Phase 2.2:\nfix CodeQL violations"| RCQ
    RCQ --> CMD
```

## Data Flow

```mermaid
flowchart LR
    classDef ai fill:#e3f2fd,stroke:#1565c0,color:#0d47a1

    API["GitHub API\ncode-scanning/alerts"]:::ai
    CLASS["Classify by type"]:::ai
    BATCH["Batch (max 5)"]:::ai
    AGENTS["Dispatch to\nspecialist agents"]:::ai
    FIX["Apply fixes"]:::ai
    VERIFY["Verify resolution"]:::ai

    API --> CLASS --> BATCH --> AGENTS --> FIX --> VERIFY
```

## Cross-References

- [github-workflows/ARCHITECTURE.md](../github-workflows/ARCHITECTURE.md) — master
  pipeline showing `/finalize-pr` Phase 2.2 invocation
- [README.md](README.md) — internal 3-tier architecture details
