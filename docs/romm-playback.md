# RomM playback recovery

RomM's library lives on the existing NFS mount. Folder names such as `Game Boy`
and `Game Boy Advance` need canonical platform bindings (`gb` and `gba`) for
EmulatorJS playback. `apps/romm/platform-bindings.yaml` owns these bindings; an
init container merges them into the persistent config while preserving other
settings. After changing bindings, run a library scan to refresh platform rows.

If the browser player reports **Network Error**, inspect the ROM content request
in RomM's logs. A 404 with `No files found for ROM` means the game record has no
file index entries, even when the ROM exists on NFS. Metadata-only scans do not
repair this condition. Run **Quick scan** across the library to reconcile file
entries with disk while preserving matched metadata and artwork. Verify the file
counts and launch representative games after the scan completes.

Game Boy, Game Boy Advance, NES, SNES, and Nintendo 64 support EmulatorJS browser
playback. GameCube, Wii, and PlayStation 2 require a compatible external emulator
or a separately configured emulator streaming service.
