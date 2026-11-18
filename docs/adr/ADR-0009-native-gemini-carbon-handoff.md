# ADR-0009: Native Gemini 4 Carbon handoff across public and private repositories

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Model routing and workflow evidence
- **Evidence Grade:** Vendor release and native client contract. Each deployment supplies its own account witness.
- **GitHub Evidence:** https://github.com/google-antigravity/antigravity-cli/releases/tag/1.5.10
- **Revisit Trigger:** A model catalog, client authentication, output schema or repository visibility change.

## Context and Problem Statement

A new agent needs enough context to continue a migration. A public repository can maintain the reusable protocol, while a private successor needs the actual source revisions, incomplete work and restore receipts. Provider model names, availability and output fields can vary by account and client.

## Decision Outcome

Use the original Antigravity client and the deployment owner's authentication. Check `agy models` in the intended launch environment. For an owner selecting Carbon High, request `gemini-4-carbon-high` explicitly. Pass a small, reviewed handoff containing the objective, authorized scope, authoritative sources, actions already taken, recovery gaps and next admissible operation. Test the recipient's interpretation using a fixture with an independently checkable answer.

Record the native client version, selected model ID, input digest, exit, duration and validated result in the private receipt. Record served model identity only if the backend supplies it. A response repeating the requested ID is a statement about the prompt. Catalog presence alone cannot qualify a production role. Keep timeouts, authentication rejections and retries with the affected role. A fallback needs an explicit owner selection. [Google model selection](https://antigravity.google/docs/models)

Publish general procedures, synthetic fixtures and their CI results in the public repository. Put machine-specific manifests and authorized operational context in the private successor. Credentials, private conversation exports and disk images stay in their approved recovery stores. Each repository verifies its own candidate commit and merge. Review public changes from a checkout containing only public history.

## Alternatives Considered

A single public handoff simplifies linking but can expose private operational history. A private-only handoff keeps sensitive records together but prevents public reuse and independent public CI. An intermediary model alias can simplify configuration while obscuring the requested provider or served identity.

## Verification Witness

Run the repository's catalog validator, merge gate and unit suite against the public changes. In the private environment, repeat the catalog lookup and native task fixture from the real caller. The receiver must distinguish the intended scope, the next operation and any condition that still prevents it. Retain the last qualified route until the new role passes its own acceptance fixture.
