# ultra_legacy_patches (lineage-20.0 / klte)

Net-diff patches that turn **plain upstream LineageOS lineage-20.0** into the LineageOS-UL / LOSUL-hacker forks,
for the 22 projects listed in `patches/MANIFEST.tsv`. The manifest (`LOSUL-hacker/android`, branch
`lineage-20.0-patchset`) syncs those 22 projects from upstream and checks this repo out at `ultra_legacy_patches/`.

## Use
    repo init -u https://github.com/LOSUL-hacker/android -b lineage-20.0-patchset
    repo sync -c -j4 --force-sync
    ultra_legacy_patches/apply-patchset.sh .      # run from the tree root; one "LOSUL patchset" commit per project
A `CONFLICT` means upstream touched the same lines: fix the markers in that project, `git add -A && git commit`.
Re-running is safe (already-applied projects are skipped). `repo sync` resets projects, so re-run after each sync.

## Update the patches after changing a project (network only, no token)
    cd ultra_legacy_patches && ./make-patchset.py     # diffs each fork in forks.json against LineageOS upstream
Only net diffs are kept (no commit history); `patches/OWN-COMMITS.txt` lists fork-only commits for reference.
The patches reproduced the forks' trees exactly when applied to upstream (generated 2026-11-07).

## Not covered (still forks in the manifest)
art, external/{jemalloc_new,perfetto,connectivity}, frameworks/libs/net, packages/modules/NetworkStack, system/bpf,
device/qcom/sepolicy-legacy, hardware/broadcom/nfc, hardware/qcom-caf/msm8974/*, system/tools/dtbtool
(no usable upstream), and hardware/ril, hardware/qcom/{display,media} (history unrelated to upstream).
