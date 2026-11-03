# Android File Server development settings

Android File Server (AFS) is disabled in the tracked defaults. This avoids
packaging an enabled file server with a missing or shared authentication token.
Unreal uses Android Debug Bridge (ADB) for Android deployment when AFS is disabled.
No desktop gameplay or renderer settings are changed.

## Developer-local opt-in

Keep AFS disabled unless it is needed for your own Android development device.
For an intentional local opt-in, use `unreal/WebHomage/Config/UserEngine.ini`,
which is ignored by Git and loads after `DefaultEngine.ini`. Use the section
`[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]`.

Before enabling `bEnablePlugin`, configure a fresh, unique, private
`SecurityToken` locally. Do not reuse a token from repository history, copy one
into source-controlled files, or enable AFS with an empty token. Do not reuse
the same token across projects or developers. Token creation/rotation and
rebuilding or replacing installed Android packages are separate, owner-approved
operations; this source change does not perform them.

Prefer USB-only development. If you need to change network or shipping behavior,
review and explicitly authorize that separately. The tracked networking,
connection-type, and shipping settings are unchanged by this fix.

Unreal Project Settings can write back into `DefaultEngine.ini`. Review
`git diff --name-only` before committing, and verify the local override is
ignored with:

```sh
git check-ignore unreal/WebHomage/Config/UserEngine.ini
```

Do not publish terminal output containing token values. AFS tokens provide only
basic, unencrypted protection and must not be treated as production-grade
authentication.

## Existing packages and repository history

Removing a tracked token does not revoke it in already-built Android packages,
erase Git history or other branches, or stop a server currently running on a
device. Existing affected Android builds need owner-approved retirement or
replacement. No Android runtime or device validation was performed for this
configuration-only change.

## References

- [Epic: Android File Server](https://dev.epicgames.com/documentation/unreal-engine/android-file-server-for-unreal-engine)
- [Epic: Configuration file hierarchy](https://dev.epicgames.com/documentation/unreal-engine/configuration-files-in-unreal-engine)

