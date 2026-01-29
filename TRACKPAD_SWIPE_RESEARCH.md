# Research: Preventing Trackpad/Mouse Swipes on macOS

## Problem Statement

On macOS, children playing Lucas' Game can accidentally swipe on the trackpad, which triggers the system gesture to change virtual desktops (Mission Control). This interrupts the game experience and can be frustrating for young users.

## Technical Context

- **Application Type**: Python-based game using Pygame
- **Display Mode**: Fullscreen (`pygame.FULLSCREEN`)
- **Platform**: macOS (with cross-platform support)
- **Current Input Handling**: Pygame event loop capturing keyboard events

## Research Findings

### Approach 1: Pygame Mouse Event Capture (RECOMMENDED)

**Description**: Use Pygame's built-in mouse event handling to capture and suppress mouse button and scroll events.

**Implementation**:
```python
# In the Pygame event loop
for event in pygame.event.get():
    if event.type == pygame.MOUSEBUTTONDOWN:
        # Capture but don't process
        pass
    elif event.type == pygame.MOUSEMOTION:
        # Capture but don't process
        pass
    elif event.type == pygame.MOUSEWHEEL:
        # Capture but don't process (Pygame 2.x+)
        pass
```

**Pros**:
- ✅ Simple to implement (a few lines of code)
- ✅ Cross-platform compatible
- ✅ No additional dependencies
- ✅ Works within existing Pygame framework
- ✅ Non-invasive to the rest of the codebase

**Cons**:
- ❌ **Limited effectiveness**: Pygame can only capture standard mouse events, NOT system-level trackpad gestures
- ❌ Does not prevent macOS system gestures (3-finger swipe, pinch-to-zoom, etc.)
- ❌ macOS Mission Control gestures happen at the OS level, before Pygame sees them

**Effectiveness**: **LOW** - Will not solve the core problem of preventing virtual desktop switching.

---

### Approach 2: macOS Fullscreen App Mode with `NSFullScreenWindowLevel`

**Description**: Ensure the Pygame window is set to proper fullscreen mode that macOS recognizes as a fullscreen application, which disables some system gestures.

**Implementation**:
Currently, the game uses:
```python
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
```

This creates a fullscreen window, but may not be recognized by macOS as a "fullscreen app" that should suppress gestures.

**Potential Enhancement**:
- Use Pygame 2.x SDL2 backend (already required)
- Ensure proper fullscreen exclusive mode

**Pros**:
- ✅ May automatically disable some macOS gestures when app is in proper fullscreen
- ✅ Native macOS behavior
- ✅ No additional code needed if properly configured
- ✅ Works with existing Pygame infrastructure

**Cons**:
- ❌ **Inconsistent behavior**: macOS may still allow Mission Control gestures even in fullscreen apps
- ❌ Depends on macOS version and system settings (user can configure gestures in System Preferences)
- ❌ Not guaranteed to work - macOS Mission Control is designed to be accessible even in fullscreen apps
- ❌ Limited control over what gets disabled

**Effectiveness**: **LOW-MEDIUM** - May reduce accidental switches but not eliminate them.

---

### Approach 3: Hide Mouse Cursor and Disable Relative Mouse Mode

**Description**: Hide the mouse cursor when the game is active to reduce accidental trackpad touches.

**Implementation**:
```python
pygame.mouse.set_visible(False)  # Hide cursor
```

**Pros**:
- ✅ Very simple (one line of code)
- ✅ Reduces visual distraction
- ✅ May discourage trackpad use
- ✅ Cross-platform

**Cons**:
- ❌ Does NOT prevent trackpad gestures
- ❌ Child can still accidentally swipe on trackpad
- ❌ Only cosmetic, doesn't address root issue

**Effectiveness**: **VERY LOW** - Does not prevent gestures, only hides cursor.

---

### Approach 4: macOS System-Level Gesture Disabling (NOT RECOMMENDED)

**Description**: Use macOS APIs (via PyObjC or similar) to programmatically disable system gestures.

**Implementation Requirements**:
- Use PyObjC to access macOS Cocoa APIs
- Attempt to modify system gesture settings
- Require elevated permissions or Accessibility access

**Example concept**:
```python
import AppKit
# Attempt to intercept gesture recognizers at system level
```

**Pros**:
- ✅ Could theoretically block all gesture inputs at system level
- ✅ Would be most comprehensive solution

**Cons**:
- ❌ **Extremely complex** - Requires deep macOS/Cocoa knowledge
- ❌ **Security restrictions** - macOS actively prevents apps from disabling system gestures
- ❌ **Requires special permissions** - May need Accessibility API access
- ❌ **Not cross-platform** - macOS-specific code
- ❌ **Additional heavy dependencies** - PyObjC, AppKit frameworks
- ❌ **May not work** - Apple intentionally makes Mission Control gestures hard to disable
- ❌ **User experience** - Users expect gestures to work; disabling them system-wide is invasive
- ❌ **Maintenance burden** - APIs can change between macOS versions

**Effectiveness**: **UNKNOWN/POTENTIALLY HIGH** - But likely blocked by macOS security.

---

### Approach 5: Configure py2app with Proper Info.plist Settings

**Description**: When building the macOS .app bundle, configure proper Info.plist settings that hint to macOS this is a fullscreen game application.

**Implementation**:
In `setup.py`, ensure proper plist settings:
```python
plist = {
    'CFBundleName': "Lucas' Game",
    'NSPrincipalClass': 'NSApplication',
    'NSHighResolutionCapable': True,
    'LSUIElement': False,  # Show in Dock
    'LSMinimumSystemVersion': '10.13.0',
}
```

**Pros**:
- ✅ Proper app configuration
- ✅ Helps macOS recognize app as legitimate fullscreen game
- ✅ No runtime overhead

**Cons**:
- ❌ Still doesn't prevent Mission Control gestures
- ❌ macOS design philosophy: gestures should always work
- ❌ Limited effectiveness

**Effectiveness**: **LOW** - Proper configuration but doesn't solve gesture problem.

---

### Approach 6: Educational/Workaround Approach (PRACTICAL RECOMMENDATION)

**Description**: Since technical solutions are limited, provide user guidance on disabling Mission Control gestures in System Preferences.

**Implementation**:
- Update documentation with instructions
- Add a startup message or README section
- Provide step-by-step guide for parents to configure macOS

**Steps for Users**:
1. Open **System Preferences** → **Trackpad**
2. Go to **More Gestures** tab
3. Uncheck "Swipe between full-screen apps" (3-finger horizontal swipe)
4. Uncheck "Mission Control" (3-finger swipe up)

Or use command line:
```bash
# Disable swipe between full-screen apps
defaults write com.apple.AppleMultitouchTrackpad TrackpadThreeFingerHorizSwipeGesture -int 0
# Disable Mission Control gesture  
defaults write com.apple.dock showMissionControlGestureEnabled -bool false
# Restart Dock to apply
killall Dock
```

**Pros**:
- ✅ **Most effective solution** - Completely prevents the problem
- ✅ User maintains control
- ✅ No code changes needed
- ✅ Works immediately and reliably
- ✅ Can be reversed easily
- ✅ Clear documentation helps parents set up the game properly

**Cons**:
- ❌ Requires user action (not automatic)
- ❌ Affects system-wide settings, not just the game
- ❌ Parents need to remember to configure before child plays
- ❌ May affect parent's workflow if they use these gestures

**Effectiveness**: **VERY HIGH** - When applied, completely solves the problem.

---

## Recommendations

### Primary Recommendation: Documentation + Basic Mouse Hiding

**What to implement**:

1. **Add mouse cursor hiding** (simple, harmless):
   ```python
   pygame.mouse.set_visible(False)
   ```

2. **Capture mouse events** (good practice, minimal help):
   ```python
   # In event loop
   elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEWHEEL):
       pass  # Capture but ignore
   ```

3. **Create comprehensive documentation** with instructions for parents:
   - Add section to README.md explaining the issue
   - Provide step-by-step System Preferences instructions
   - Include command-line options for advanced users
   - Explain why this is necessary (macOS security design)

### Why This Approach?

- **Technical reality**: macOS is designed to keep Mission Control gestures accessible at all times for accessibility reasons
- **Security**: Apple prevents apps from programmatically disabling system gestures
- **Pragmatic**: User configuration is the most reliable solution
- **Simple**: Minimal code changes, no complex dependencies
- **Transparent**: Users understand what's happening and maintain control

### Not Recommended

- ❌ Complex macOS-specific gesture interception (likely impossible, high effort, low chance of success)
- ❌ PyObjC-based system modifications (security restrictions, maintenance burden)
- ❌ Attempting to fight against macOS design philosophy

## Implementation Summary

**Recommended changes**:
1. Hide mouse cursor during gameplay
2. Add mouse event handlers (for consistency, though limited effectiveness)
3. Document the issue and provide clear user instructions
4. Test on macOS to verify baseline functionality

**Expected outcome**: 
- Minor improvements from cursor hiding
- Complete solution available through user configuration
- Clear guidance for parents setting up the game

## References

- [Pygame Mouse Documentation](https://www.pygame.org/docs/ref/mouse.html)
- [macOS Human Interface Guidelines - Gestures](https://developer.apple.com/design/human-interface-guidelines/inputs/touchpad-gestures)
- [SDL2 Fullscreen Modes](https://wiki.libsdl.org/SDL2/SDL_SetWindowFullscreen)

---

*Research completed: January 29, 2026*
