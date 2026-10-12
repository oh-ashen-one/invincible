// Homage fan game tooling (not affiliated with Marvel/Sony/Insomniac). P6 city life: minimal AppKit launch probe used by gui_ok.sh.
// Unreal (any binary, -nullrhi commandlets included) starts its engine loop from NSApplication's applicationDidFinishLaunching. When the macOS WindowServer has been restarted
// by its watchdog and the session is not back (2026-09-30 06:55), that callback never fires and every engine hangs at ~0.9 s CPU without a log line. This program prints
// "didFinishLaunching" and quits when an app can launch, and hangs after "running" when it cannot.
import AppKit
class D: NSObject, NSApplicationDelegate {
  func applicationDidFinishLaunching(_ n: Notification) { print("didFinishLaunching"); fflush(stdout); NSApp.terminate(nil) }
}
let app = NSApplication.shared
let d = D(); app.delegate = d
print("running"); fflush(stdout)
app.run()
