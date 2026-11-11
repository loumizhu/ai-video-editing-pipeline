# Human Approval Record — Gate <G1|G2|G3|G3b|G4>

- **Gate ID:** `G<N>_<Gate_Slug>`
- **Project Folder:** `Videos-Scripts/<NN>_<Video_Title>/`
- **Reviewed Stage:** `<NN>_<Stage_Name>`
- **Decision:** `APPROVED` | `REJECTED_WITH_REVISIONS`
- **Reviewed By (Human):** `<Human Approver Name>`
- **Timestamp:** `<YYYY-MM-DD HH:MM>`

---

## Approved Artifacts & Hash Manifest

> **RULE:** AI agents cannot self-approve or write this record. Downstream execution requires this exact file signed by the human operator with verified SHA-256 hashes on disk.

Compute hash in PowerShell: `Get-FileHash -Algorithm SHA256 "path/to/artifact"`

```yaml
gate: G<N>_<Gate_Slug>
decision: APPROVED
approved_by: "<Human Approver Name>"
approved_at: "<ISO-8601 Timestamp>"
artifacts:
  - path: "<relative/path/to/artifact_1>"
    sha256: "<64-character-sha256-hex>"
  - path: "<relative/path/to/artifact_2>"
    sha256: "<64-character-sha256-hex>"
notes: |
  <Human feedback, rationale, or adjustments required>
```

---

## Verification Checklist (Human)
- [ ] Confirmed topic/hook/script meets household-name star/franchise standard.
- [ ] Owner checked packaging is about the video's real subject.
- [ ] Verified narrative integrity, truth tiers, and retention architecture.
- [ ] Confirmed all listed artifact checksums match the disk contents.
