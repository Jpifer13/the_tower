# An immersive space hides every other app

**Status: verified on visionOS 26.5, 2026-09-03. This constrains the product, not just the code.**

## The finding

A third-party app cannot act as a backdrop that other apps float inside. The moment your
app opens an `ImmersiveSpace`, every other app disappears — including video calls.

Apple states it plainly in the `openImmersiveSpace` documentation:

> When your app opens an immersive space, the system hides all other visible apps.

## Why the docs look like they contradict this

`ImmersionStyle.mixed` is described as:

> An immersion style that displays unbounded content intermixed with **other app content**,
> along with passthrough video.

That reads like other apps stay visible. They do not. "Other app content" means other scenes
belonging to *your* app — your own windows and volumes coexist with your immersive content.

## How it was verified

Empirically, in the visionOS 26.5 simulator, with `.mixed` (the most permissive style):

1. Launch Safari — its window sits directly ahead.
2. Launch The Tower, which opens a mixed immersive space.
   → Safari's window is **gone**. Passthrough is still visible; our own window and 3D content render.
   Safari is still *running* (`launchctl list` shows the process alive) — it is only hidden.
3. Launch Safari again while the immersive space is open → still not rendered.
4. Terminate The Tower.
   → Safari's window reappears **in the same position it always occupied**, proving it was
   being occluded by the immersive space rather than positioned somewhere out of view.

Screenshots of each step are in the session scratchpad.

## The system Environments are privileged

Apple's own Environments (Mount Hood, the Moon, and so on, on the Digital Crown) are *not*
immersive spaces. They're a system feature, and third parties cannot publish into that picker.
Shipping apps hit this same wall: Disney+'s Avengers Tower and HBO Max's Harry Potter
environment are usable only inside those apps.

visionOS 26 adds `Scene.immersiveEnvironmentBehavior(_:)` with `.coexist` and `.replace`.
This controls how *your* immersive space interacts with Apple's *system* environment — it does
not let other apps into your space, and it isn't a route to publishing an Environment.

## What this means for The Tower

The build plan's premise — "sit and work with your other apps floating in the room", and
App Store screenshots showing app windows inside the tower — is not achievable as written.

Anything the user does inside the tower has to be provided by The Tower itself.
