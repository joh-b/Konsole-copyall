# Konsole Custom — Copy All

This repository packages an isolated `konsole-custom` launcher with one
additional native Konsole action:

```text
Copy Entire Scrollback
action id: copy-entire-scrollback
```

The action synchronously selects every line still retained by the active
terminal session and copies it to the regular clipboard. It does not synthesize
input, use D-Bus clipboard export, enable automatic copy-on-selection, or copy
to the primary selection.

No default shortcut is compiled into Konsole. Assign one through Konsole
Custom's shortcut configuration after installing the package.

The public package does not install `bin/konsole` or
`org.kde.konsole.desktop`, so it does not shadow a system Konsole package. It
provides exactly these public entry points:

```text
bin/konsole-custom
share/applications/org.kde.konsole-custom.desktop
```

The patched application uses `org.kde.konsole-custom` as its desktop identity
and D-Bus service base name, so its service is separate from the one used by a
system Konsole. A unique desktop-launched instance registers exactly that name;
upstream's multiple-instance mode appends the process ID. It deliberately
retains upstream's internal application name and `bin/konsole` layout: Konsole
uses that application name to distinguish the full terminal from an embedded
KPart. The non-shadowing public wrapper is the only package intended for normal
installation.

## Source and package pin

The production dependency set is pinned by `flake.lock`. The Konsole release,
source URL, and source hash are pinned separately in `nix/upstream.json`, so a
consumer and CI evaluate the same derivation. This is an unofficial downstream
modification. The source patches are intentionally limited to:

- `src/main.cpp`
- `src/terminalDisplay/TerminalDisplay.h`
- `src/terminalDisplay/TerminalDisplay.cpp`
- `src/session/SessionController.cpp`

The flake exports:

```text
packages.x86_64-linux.konsole-copy-entire-scrollback
packages.x86_64-linux.patched-konsole
packages.x86_64-linux.konsole-custom
packages.x86_64-linux.default
```

`default` and `konsole-custom` are the non-shadowing public package.
`patched-konsole` and the compatibility alias
`konsole-copy-entire-scrollback` expose the internal upstream-layout package for
development and validation.

## Build

```console
nix flake check
nix build .#default
```

`nix flake check` verifies both patches, builds the patched package, checks its
compiled action and identity markers, and asserts that the public output
contains only `konsole-custom` and its separate desktop entry. The desktop
check specifically requires an absolute `Exec=…/konsole-custom --new-tab`
action. A weekly compatibility workflow can also test an explicitly supplied
nixpkgs ref without changing the production lock file.

## NixOS stable maintenance

The flake always selects a numbered final NixOS stable branch. GitHub Dependabot
refreshes `flake.lock` from that same branch weekly. A separate merge workflow
accepts only a successful **Check** run for an open `dependabot[bot]` Nix PR that
changes exactly `flake.lock` and preserves the currently selected numbered
branch. It then merges that exact tested commit automatically. Dependabot cannot
change the pinned ref in `flake.nix`, so a newly created pre-release branch
cannot change the selected release early.

The daily **Promote latest NixOS stable** workflow separately reads official
`NixOS/nixpkgs` tags and accepts only final `YY.05` or `YY.11` tags. When a newer
final release exists, it updates `flake.nix`, the compatibility-workflow default,
and `flake.lock` together on a pull-request branch. It dispatches the complete
**Check** workflow for that exact commit and merges the PR only if the check and
explicit default-package build pass. It then requires a successful publish
workflow for the resulting `main` revision. A failed or missing publish run is
retried by the next daily promotion check, even when no newer NixOS release is
available.

Committing `.github/dependabot.yml` enables GitHub's native Dependabot version
updates; Mend Renovate is not required. The release-transition and Dependabot
merge workflows use only the repository's `GITHUB_TOKEN`; repository Actions
settings must allow workflows to create and merge pull requests.

## Upstream release tracking

The nightly **Track upstream releases** workflow reads tags from the official
`KDE/konsole` repository. It ignores malformed tags and KDE beta/RC tags,
prefetches the stable release tarball, records its content hash, refreshes the
locked nixpkgs revision, then runs the complete flake check and public-package
build. The Cachix action is configured as pull-only while validation runs. When
and only when all checks succeed, the workflow explicitly pushes the complete
result closure to the configured Cachix cache and commits the verified
`nix/upstream.json` and `flake.lock` updates to `main`.

An incompatible patch, missing release tarball, missing Cachix setting, build
failure, or concurrent change to `main` prevents the version update. The next
nightly run tries again. Because the tracker performs the build and publication
itself, it does not depend on a second workflow being triggered by its
`GITHUB_TOKEN` commit.

The repository's Actions policy and branch rules must permit the workflow token
to update `main`. If they do not, the verified closure is still cached, but the
final push fails and the pinned version remains unchanged.

## Binary cache publication

GitHub Actions builds every change to `main`. To also publish the complete Nix
closure to Cachix, configure both of these repository settings:

- Repository variable `CACHIX_CACHE_NAME`: the Cachix cache name.
- Repository secret `CACHIX_AUTH_TOKEN`: a write token for that cache.

Without both values, the workflow still validates and builds the package but
reports that publication was skipped. A GitHub Actions cache or build artifact
is not a Nix substituter. When both settings exist, the workflow explicitly
pushes the default package and its complete runtime closure.

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
konsoleCustom =
  inputs.konsole-copyall.packages.${pkgs.stdenv.hostPlatform.system}.default;
```

Changing the nixpkgs input produces a different derivation and normally causes
a binary-cache miss and local compilation.

Installing that package makes `org.kde.konsole-custom.desktop` available to the
desktop environment. Plasma panel configuration can refer to it as
`applications:org.kde.konsole-custom.desktop`; the package supplies the desktop
entry, while the choice to pin it to a particular panel remains local desktop
state.

## Runtime validation

CI proves that the patch applies and compiles, but it cannot establish clipboard
behavior in a graphical desktop session. Validate with an explicitly separate
patched process so an already-running unpatched Konsole instance is not reused:

```console
./result/bin/konsole-custom --separate
```

In that process, confirm that **Copy Entire Scrollback** appears in
**Settings → Configure Keyboard Shortcuts**, assign the intended shortcut, and
test a history containing unique start and end markers. Both markers must be in
the regular clipboard after invoking the action once.

Only scrollback still retained by Konsole can be copied. Output already removed
by a finite history limit cannot be recovered.

## License

The patches and this repository's original material are licensed under
`GPL-2.0-or-later`. Every modified upstream source file must carry that same
SPDX identifier or the build stops before applying a patch:

- [`main.cpp`](https://github.com/KDE/konsole/blob/master/src/main.cpp)
- [`SessionController.cpp`](https://github.com/KDE/konsole/blob/master/src/session/SessionController.cpp)
- [`TerminalDisplay.cpp`](https://github.com/KDE/konsole/blob/master/src/terminalDisplay/TerminalDisplay.cpp)
- [`TerminalDisplay.h`](https://github.com/KDE/konsole/blob/master/src/terminalDisplay/TerminalDisplay.h)

The complete license text is in `LICENSES/GPL-2.0-or-later.txt`. This repository
does not relicense Konsole or its dependencies; their existing copyright and
license notices continue to apply.

The corresponding source and build information for a cached binary consists of
the pinned upstream source above, the patches in `patches/`, and the Nix build
definition and lock file in this repository.
