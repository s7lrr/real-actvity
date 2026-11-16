# Installation notes

The recommended end-user distribution is `PresenceStudio-Setup.exe`, produced by the GitHub Actions workflow.

The installer deploys a self-contained executable. The end user does not need to install Python or application libraries.

The application still requires the Discord desktop client to be running because Rich Presence RPC uses Discord's local IPC connection. This desktop requirement is separate from the application's bundled dependencies.
