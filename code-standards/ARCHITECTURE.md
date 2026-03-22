# code-standards — Architecture

Passive knowledge plugin providing code quality and review standards. These skills are
loaded on demand — they do not run automatically like hooks.

## Integration Map

```mermaid
flowchart LR
    classDef ai fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
    classDef external fill:#f3e5f5,stroke:#6a1b9a,color:#4a148c

    subgraph standards["code-standards (this plugin)"]
        CQS["/code-quality-standards\nPEP 8, TypeScript, security,\nTDD, testing philosophy"]:::ai
        RS["/review-standards\nReview process, feedback\nformat, severity levels"]:::ai
    end

    subgraph consumers["Skills that load these standards"]
        RPT["/resolve-pr-threads\n(github-workflows)"]:::external
        TAR["/trigger-ai-reviews\n(github-workflows)"]:::external
        RCR["superpowers:\nrequesting-code-review\n(superpowers)"]:::external
        SIMP["/simplify\n(external)"]:::external
    end

    CQS -.->|"informs code writing"| SIMP
    RS -.->|"informs review process"| RPT
    RS -.->|"informs review setup"| TAR
    CQS -.->|"informs quality checks"| RCR
```

## Passive vs Active

Standards plugins provide context when loaded — they do not block, intercept, or
modify operations. For active enforcement of coding patterns, see
[git-guards/ARCHITECTURE.md](../git-guards/ARCHITECTURE.md) and
[content-guards/ARCHITECTURE.md](../content-guards/ARCHITECTURE.md).
