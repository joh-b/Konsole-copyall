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

No default shortcut is compiled into Konsole. Assign one through Konsole's
shortcut configuration after installing the package.

## Source and package pin

The production flake is locked to nixpkgs commit
`8eeec934ae0dbeca3d7868c059568a65c08b2fc3` from `nixos-26.05`. That revision
packages [KDE Konsole `26.04.3`](https://github.com/KDE/konsole/tree/v26.04.3).
This is an unofficial downstream modification. The source patch is
intentionally limited to:

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
behavior in a graphical desktop session. Validate with an explicitly separate
patched process so an already-running unpatched Konsole instance is not reused:

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

The patch and this repository's original material are licensed under
`GPL-2.0-or-later`. Each modified file in Konsole `26.04.3` carries that same
SPDX license identifier:

- [`SessionController.cpp`](https://github.com/KDE/konsole/blob/v26.04.3/src/session/SessionController.cpp)
- [`TerminalDisplay.cpp`](https://github.com/KDE/konsole/blob/v26.04.3/src/terminalDisplay/TerminalDisplay.cpp)
- [`TerminalDisplay.h`](https://github.com/KDE/konsole/blob/v26.04.3/src/terminalDisplay/TerminalDisplay.h)

The complete license text is in `LICENSES/GPL-2.0-or-later.txt`. This repository
does not relicense Konsole or its dependencies; their existing copyright and
license notices continue to apply.

The corresponding source and build information for a cached binary consists of
the pinned upstream source above, the patch in `patches/`, and the Nix build
definition and lock file in this repository.
