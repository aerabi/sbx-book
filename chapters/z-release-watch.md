\newpage

# Appendix: SBX Release Watch

The exercises in this book were written against sbx v0.51.0. A scheduled cloud sandbox, set up in Chapter 3, checks for new stable sbx releases every day and proposes an update to this appendix. The entries summarize release notes only. Nobody re-ran the exercises against these versions; treat each entry as a hint about where commands may have changed.

Latest release checked: **v0.54.1** (2026-11-24).

## Likely CLI Changes

### v0.54.1 (2026-11-24)

- Chapter 2: On macOS, secrets saved before an upgrade can now be removed through SBX without manually deleting their Keychain entries.

[Release notes](https://github.com/docker/sbx-releases/releases/tag/v0.54.1)

### v0.54.0 (2026-11-16)

- Chapter 2: `sbx policy check network` identifies the rule that allowed a target and explains when further evaluation is needed.
- Chapter 2: Kit validation checks inherited configuration and reports inherited warnings. Existing kit permissions may require confirmation again after upgrading.
- Chapter 2: OAuth secret sign-in respects `--no-input`. Declining secret replacement now returns a nonzero exit status.
- Chapter 3: Cloud creation accepts TTL values from 15 seconds to 24 hours and rejects explicitly empty timeout actions and sandbox names before provisioning. A kit’s network allow list preserves the account policy when neither `--allow-network` nor `--deny-network` is supplied.
- Chapter 3: Declining a sandbox move returns a nonzero exit status, and an explicitly empty destination name is rejected before the move starts.
- Chapter 3: Scheduled runs accept `--workdir` and `-w`, and schedule durations accept case-insensitive units.

[Release notes](https://github.com/docker/sbx-releases/releases/tag/v0.54.0)

### v0.53.0 (2026-11-11)

- Chapters 1 and 3: The built-in `gemini` agent was retired. Existing Gemini sandboxes keep running, but `sbx move` cannot move them.
- Chapter 1: `sbx run <agent> -- <args>` preserves the image’s entrypoint arguments. Omit a subcommand already included in the entrypoint to avoid running it twice.
- Chapters 1 and 2: HTTP policy matching treats ASCII letters in URL paths and query parameter names and values case-insensitively. Policy checks accept `-v` for `--verbose`.
- Chapter 2: Kits granted `ports.publish` with `approval: none` can request an automatically assigned loopback port without prompting. Fixed host ports still require approval.
- Chapter 3: `sbx --cloud schedule` manages recurring tasks, including manual runs, run history, and pausing or resuming schedules.
- Chapter 3: `sbx move` rejects occupied explicit destination names before capturing or transferring the source. `--name` specifies the exact destination name.

[Release notes](https://github.com/docker/sbx-releases/releases/tag/v0.53.0)
