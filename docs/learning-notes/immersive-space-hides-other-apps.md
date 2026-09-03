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

## The exception: Mac Virtual Display (developer toggle)

There is one documented way through, and it is worth knowing because it solves the
*personal* use case even though it can't ship.

On the device: **Settings → Privacy & Security → Developer Mode** (on, then restart), then
**Settings → Developer → Allow Mac Virtual Display**. With that enabled, the Mac Virtual
Display persists inside third-party immersive experiences. You can enter The Tower, summon
your Mac desktop from Control Center, and work at a terminal inside the room.

Limits worth being precise about:

- It is **Mac Virtual Display only** — your Mac's screen. Native visionOS apps are still hidden.
  A meeting works only if the meeting is on the Mac.
- It is behind **Developer Mode**, which is not something to ask a paying customer to enable.
  Fine as a documented power-user note; not a feature the product can be sold on.

## Shared Space is not an alternative for an enclosing room

The obvious workaround — "skip the immersive space, run in the Shared Space so other apps
coexist" — does not give you a room you are inside.

In the Shared Space an app gets windows and **volumes**, and Apple defines a volume as
displaying "3D content within a **bounded region**". Unbounded content is the defining
property of an `ImmersiveSpace`: "A scene that presents its content in an **unbounded space**."

So a Shared Space version of The Tower would be a diorama in a box sitting in your real room —
not a tower you sit in, and certainly not one you can pace around. The enclosing room and
coexisting apps are mutually exclusive for third-party apps.

## What this means for The Tower

The build plan's premise — "sit and work with your other apps floating in the room", and
App Store screenshots showing app windows inside the tower — is not achievable as written.

For anyone who hasn't enabled Developer Mode — i.e. every normal customer — whatever they do
inside the tower has to be provided by The Tower itself.

For **you**, with the developer toggle on, the office concept genuinely works: tower plus Mac
Virtual Display plus Ghostty. That makes it a viable personal tool regardless of what the
shipped product turns out to be.
