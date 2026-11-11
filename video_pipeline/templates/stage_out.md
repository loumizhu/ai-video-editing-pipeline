# Stage Output — Stage <NN>: <Stage_Name>

- **Worker:** `<Agent Name>`
- **Stage:** `<NN>_<Stage_Name>`
- **Timestamp:** `<YYYY-MM-DD HH:MM>`
- **Pass:** `<1 | 2 | 3>`

## 1. Deliverable Summary
- <Bullet 1: Concrete finding, outcome, or asset summary>
- <Bullet 2: Specific metrics or structures established>
- <Bullet 3: Next stage handoff readiness>

## 2. Output Files & Artifact Hashes
| Output File Path (Relative to Video Folder) | SHA-256 Checksum | Verified On Disk |
|---|---|---|
| `<exact/target/file_1>` | `<sha256>` | Yes |
| `<exact/target/file_2>` | `<sha256>` | Yes |

## 3. Tool Commands Executed
```bash
# Record exact deterministic CLI tool executions with return status
<tool command 1>  # return code 0
<tool command 2>  # return code 0
```

## 4. Verification & Self-Check
- [x] All upstream inputs read directly from disk.
- [x] Exact output file naming adhered to (no "FINAL", no unnumbered drafts).
- [x] Narrative / operational rules strictly preserved.
- [x] Deterministic CLI tasks separated from agent analysis.

## 5. Notes & Open Questions
- <Any edge cases or caveats for the reviewer or orchestrator.>

<span style="color: purple;">[AI Agent]</span>
