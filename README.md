# Konsole Copy All

This repository packages Konsole with one additional native action:

```text
Copy Entire Scrollback
action id: copy-entire-scrollback
```

The action synchronously selects every line still retained by the active
terminal session and copies it to the regular clipboard. It does not synthesize
input, use D-Bus clipboard export, enable automatic copy-on-selection, or copy
to the primary selection.

No default shortcut is compiled into Konsole. Assign a shortcut such as
`Ctrl+Alt+K` through Konsole's shortcut configuration after installing the
package.

## Source and package pin

The production flake is locked to nixpkgs commit
`8eeec934ae0dbeca3d7868c059568a65c08b2fc3` from `nixos-26.05`. That revision
packages Konsole `26.04.3`. The source patch is intentionally limited to:

- `src/terminalDisplay/TerminalDisplay.h`
- `src/terminalDisplay/TerminalDisplay.cpp`
- `src/session/SessionController.cpp`

The flake exports:

```text
packages.x86_64-linux.konsole-copy-entire-scrollback
packages.x86_64-linux.default
```

## Build

```console
nix flake check
nix build .#default
```

`nix flake check` verifies the patch structure, builds the patched package, and
checks the installed result for both the action identifier and its visible
label. A weekly compatibility workflow tries the latest `nixos-26.05` revision
without changing the production lock file.

## Binary cache publication

GitHub Actions builds every change to `main`. To also publish the complete Nix
closure to Cachix, configure both of these repository settings:

- Repository variable `CACHIX_CACHE_NAME`: the Cachix cache name.
- Repository secret `CACHIX_AUTH_TOKEN`: a write token for that cache.

Without both values, the workflow still validates and builds the package but
reports that publication was skipped. A GitHub Actions cache or build artifact
is not a Nix substituter.

Consumers must configure the resulting Cachix URL and public signing key as
trusted substituter settings. The cache page supplies the exact public key;
do not guess it.

## Consume the pinned package

Use the package's own locked nixpkgs input so that its derivation matches the
one built by CI. Do not initially make this input's nixpkgs follow a different
consumer input:

```nix
inputs.konsole-copyall.url = "github:joh-b/Konsole-copyall";

# Later, where packages are selected:
inputs.konsole-copyall.packages.${pkgs.system}.default
```

Changing the nixpkgs input produces a different derivation and normally causes
a binary-cache miss and local compilation.

## Runtime validation

CI proves that the patch applies and compiles, but it cannot establish clipboard
behavior in a particular Plasma Wayland session. Validate with an explicitly
separate patched process so an already-running unpatched Konsole instance is not
reused:

```console
./result/bin/konsole --separate
```

In that process, confirm that **Copy Entire Scrollback** appears in
**Settings → Configure Keyboard Shortcuts**, assign the intended shortcut, and
test a history containing unique start and end markers. Both markers must be in
the regular clipboard after invoking the action once.

Only scrollback still retained by Konsole can be copied. Output already removed
by a finite history limit cannot be recovered.

## License

The patch and repository are licensed under `GPL-2.0-or-later`, matching
Konsole's modified source files. See `LICENSES/GPL-2.0-or-later.txt`.
