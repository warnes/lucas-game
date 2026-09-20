# Disabling the Touch Bar — design note

**Status: not implemented.** This document exists so the work can be picked up
later without re-deriving the constraints. No behaviour has changed.

## What is already handled

`lucas_game.py` remaps the system media and brightness keys to F13 via `hidutil`
while the game runs (`_suppress_media_keys()`). The project's claim — recorded in
the code comment and in `README.md` — is that the Touch Bar emits the *same HID
consumer-page usages* as the physical media keys, so tapping volume or brightness
on the Touch Bar is already swallowed.

That claim has **not been re-verified on hardware for this note.** It is
plausible and it is what the existing code asserts; treat it as the project's
position, not as something this document confirms.

## What is not handled

Everything else the Touch Bar can do. Even with media keys remapped, a child
touching the strip can still reach, depending on the current presentation mode:

- The **Escape** region.
- **App-specific controls**, whenever a focused app publishes an `NSTouchBar`.
- The **Control Strip** — Siri, Spotlight, Do Not Disturb, and the expanded
  brightness/volume sliders, which are Touch Bar UI rather than key events and so
  are not necessarily covered by the `hidutil` remap.
- Simply **lighting up and being interesting**, which for the target user is
  most of the problem.

The goal for a kiosk is a Touch Bar that is dark and inert for the duration of
the game, and exactly as it was afterwards.

## What was verified on this machine

Checked 2026-08-31 on the development machine (`MacBookPro16,1`, 2019 16-inch,
Intel, macOS Darwin 25.6.0):

- The hardware **has** a Touch Bar, so this is testable here rather than needing
  a second machine.
- The `com.apple.touchbar.agent` preferences domain exists and is readable:

  ```
  PresentationModeGlobal = appWithControlStrip;
  PresentationModeFnModes = { appWithControlStrip = functionKeys; };
  ```

- `/System/Library/CoreServices/TouchBarServer.app` **does not exist** at that
  path on this macOS version. Recipes found online that `killall TouchBarServer`
  or reference that bundle are written against older releases and should not be
  copied without checking. The current process name was not established.

## Candidate approaches, with honest confidence

| Approach | Confidence | Notes |
|---|---|---|
| `defaults write com.apple.touchbar.agent PresentationModeGlobal <mode>` and restart the agent | Medium | The domain and both keys are confirmed present here. Which modes are valid on this macOS, and which agent to restart, are **not** established — the classic `TouchBarServer` path is gone. Needs experiment. |
| Publish an empty `NSTouchBar` for our own app (PyObjC) | Low–Medium | Well-defined for a Cocoa app, but pygame/SDL windows may not participate, and it cannot suppress the Control Strip, which is system-owned. Adds a PyObjC dependency to the `.app` bundle. |
| Extend the `hidutil` remap to more usages | Low | Only helps for inputs delivered as HID key events. Control Strip taps are not obviously in that class. |
| Fully "turn off" the Touch Bar | Unknown | No supported public API is known to the author. Do not assume one exists without finding it. |

Start with the first one, because it is the only candidate whose preconditions
are already confirmed on the target hardware.

## Constraints any implementation must satisfy

These are not style preferences. Every one of them is a defect that was found in
the media-key feature by the committee review on 2026-08-31, in code that looked
correct and passed a green test suite. The Touch Bar work touches the same class
of state — global, user-visible, outside the process — so it will reproduce them
unless they are designed for up front.

1. **Do not fire on import.** The media-key teardown was registered with `atexit`
   at module scope and guarded only on the platform, so merely importing the
   module — which `pytest` does at collection — mutated system-wide state at
   interpreter exit. Bind setup and teardown to the operation, not to the
   interpreter's lifetime.
2. **Read before you write, and put back what was there — not a default.** The
   media-key "restore" set `UserKeyMapping` to `[]`, which is a wipe, not a
   restore: it destroyed remaps the game never made. `PresentationModeGlobal` is
   a single global value with exactly the same shape. Capture the prior value,
   restore *that*; if it cannot be read, do not change it.
3. **Refuse rather than clobber.** Where prior state cannot be preserved, skip
   the feature and say so. A child reaching the Control Strip is recoverable; a
   parent's customisation silently destroyed is not.
4. **Never raise out of a teardown path.** It runs from `atexit` and from the
   `SIGTERM` handler; an escaping exception leaves the machine altered with no
   cleanup.
5. **Survive `SIGKILL` legibly.** Cleanup cannot run. Document the one-line
   manual reset in `README.md`, as the media-key section does.
6. **Test it, and watch the test fail first.** The entire media-key mechanism had
   exactly one reference in the suite, and that reference monkeypatched it away.
   Assert the argv of every external command, and assert that teardown is a
   **no-op when setup never ran** — that is the assertion that would have caught
   the import-time wipe.
7. **Non-macOS must be a clean no-op.** The Raspberry Pi target runs the same
   file; guard on `platform.system() == "Darwin"` as the existing code does.

## Open questions

- Does the existing `hidutil` remap already cover Touch Bar media taps? Verify on
  hardware before adding anything, in case part of this is already solved.
- Which presentation mode gives the darkest, least interactive strip, and is it
  settable per-session rather than persistently?
- Which process must be restarted for a `defaults write` to take effect on this
  macOS, given `TouchBarServer.app` is absent?
- Does the setting survive a reboot? If it does, cleanup failure is a persistent
  change to the user's machine and needs the `SIGKILL` note to be prominent.
- Is this worth doing at all, given the child would have to reach past the
  keyboard? Scope it against the actual risk before building it.
