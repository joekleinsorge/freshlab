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

On October 15, 2026, Quick Scan restored 512 missing file entries across 533
games on eight platforms. All indexed files were readable and matched their
recorded sizes. Browser launches reached game screens for Pokémon Gold,
Pokémon FireRed, Tetris (NES), NHL Breakaway 99 (N64), and Super Mario World
(SNES). The Game Boy and Game Boy Advance platform rows now use `gb` and `gba`.

Game Boy, Game Boy Advance, NES, SNES, and Nintendo 64 support EmulatorJS browser
playback. GameCube, Wii, and PlayStation 2 require a compatible external emulator
or a separately configured emulator streaming service.
