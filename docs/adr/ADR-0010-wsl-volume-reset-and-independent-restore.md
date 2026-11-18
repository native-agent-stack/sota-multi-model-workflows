# ADR-0010: Independent recovery before a WSL host volume reset

- **Status:** Accepted
- **Date:** 2026-11-17
- **Layer:** Workstation storage and service continuity
- **Evidence Grade:** Upstream WSL lifecycle and Windows backup interfaces. Restore proof is specific to each deployment.
- **GitHub Evidence:** https://github.com/microsoft/WSL/releases/tag/3.0.5
- **Revisit Trigger:** A storage, distribution, backup target, service-owner or model handoff change.

## Context and Problem Statement

A Windows volume can hold registered WSL distributions alongside application data disks, shared working directories, swap, backups and unrelated user files. A verified Git branch can recover tracked code while unpushed commits, native databases and untracked material still depend on the original storage.

## Decision Outcome

1. Inventory the entire volume and identify its physical disk, partition and volume identity. Map registered distributions, additional VHDs, swap configuration, VHD mount ownership, ordinary files and unreadable areas. Keep file names and machine identities in a private manifest. Recheck the target identity immediately before cutover.
2. Preserve recoverable copies on independent storage. Capture the permissions and filesystem metadata required by the selected recovery method. Use an application-consistent backup or quiesce the relevant writers for final capture. A copy of a mounted, changing virtual disk is insufficient evidence for a clean application restore. WSL distribution export covers that distribution's filesystem. Additional data disks, host configuration and external volumes need separate coverage. [Microsoft WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)
3. Restore from the backup into a distinct target. Confirm file digests, repository history, native database integrity and required ownership. Verify that the restored guest has isolated ports, schedulers, credentials and external side effects **before its first boot**. Start a clean vendor image or a deliberately isolated guest for the service rehearsal. [Windows backup and recovery](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/wbadmin-start-recovery)
4. Ask each active service owner to hand over its writer in a maintenance window. Retain one active writer per external resource. Switch traffic only after checking the successor through its normal entry point and rehearsing rollback. Record final backup identifiers, coverage gaps, restored checks and owner authorization privately. Volume erasure requires a separate target-specific decision once these conditions hold.

## Alternatives Considered

A distribution-only export works for a guest-only move. It leaves other material on a shared volume outside the recovery set. A whole-volume image covers more storage, but its usefulness depends on independent media, application consistency and a tested restoration. A clean base image reduces inherited configuration while still requiring the owner's private state and native sign-in.

## Verification Witness

A recovery receipt identifies the source and destination, capture method, excluded or inaccessible content, service baseline, independent restore and rollback result. Exercise one failed canary before accepting a cutover. A CI success for these documents certifies the repository revision. The host owner records the separate recovery and cutover evidence.
