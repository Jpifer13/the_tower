# Full immersion has a 1.5 m leash — mixed doesn't

**Verified against Apple documentation, 2026-09-03. This decides the immersion style and the room size.**

## The constraint

From *Creating fully immersive experiences*:

> When you start a fully immersive experience, visionOS defines a system boundary that extends
> approximately 1.5 meters from the initial position of the person's head. If their head moves
> outside of that zone, the system automatically stops the immersive experience and turns on the
> external video again.

A 1.5 m radius — a 3 m circle. It is a safety assistant, and for `.full` it is outside the
developer's control. Pacing around during a call would repeatedly eject you from the tower.

## The way around it: mixed immersion + an enclosing room

`.mixed` does not apply the boundary. You keep passthrough, but if the room model **fully
encloses** you — walls, floor, ceiling — the geometry occludes the real world anyway, and you get
what looks like full immersion with no leash.

This is why The Tower uses **`.mixed`**, not `.full`. It costs nothing visually, given the room
is a closed volume by design.

It also stacks with the other constraint: Mac Virtual Display (via Developer Mode) is what makes
the office concept work, and that is independent of immersion style.

## The safety trade, stated plainly

Turning off the leash means **visionOS will not stop you walking into real furniture.** A developer
on Apple's forums reported knocking over a lamp and walking into a wall doing exactly this.

For a personal tool used in a known room, that is an informed choice. It does mean:

- **Keep a genuinely clear physical area.** The virtual floor will hide the real one.
- **Size the virtual room to the real one.** If the tower is 6 m across and your clear floor is
  3 m, you will walk into a wall that isn't there — or rather, one that is.
- Reconsider this if a generic App Store version ever happens; strangers won't know the rule.

## Consequence for the design

The pacing requirement is not limited by visionOS once we're on `.mixed`. It is limited by the
real room. So the tower's walkable area should be sized from the actual clear floor space
available, not chosen for looks.
