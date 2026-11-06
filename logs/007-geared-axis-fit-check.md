# 007 — Geared-axis fit check

## 2026-11-05 — design rounds r01 to r03

Goal: add a StepperOnline EG17-G5 5:1 planetary reducer to the moteus
developer kit, held by custom fixtures, and check the fit with unpowered
PETG prints before anything is machined.

r01 was a faceplate and support study. r02 brought the stand, support,
and hub into one layout. The vendor review then exposed a cable
interference and a fastener-access problem, which r03 resolves. r03 is
the fit-check candidate. All four parts are in `cad/r03/` as STEPs and
print STLs, built from the vendor models with a parametric CadQuery
script (`hello_motion_fitcheck_r03.py`).

### The four parts (nominal CAD dimensions, mm)

- **Companion hub** — Ø28 × 4 flange, Ø18 × 12 neck, Ø5 × 14.5 exposed
  stub. Total length 30.5 from the rotor face. Three Ø3.3 holes on Ø17
  PCD. The Ø5 stub enters the gearbox input bore with 6 mm nominal
  engagement and 1 mm to the end of its cylindrical section.
- **Actuator stand** — envelope 90 × 110 × 65. Open-front base, 8 thick.
  Two cheeks, 14 × 12 × 57. Four Ø3.3 bracket holes. Cable pocket
  X −21 to −13, Y −15 to +15, floor Z 6.5, clearing the modeled motor
  cable by 1.03 mm.
- **Gearbox support** — envelope 44 × 84 × 79, with the faceplate built
  in. Faceplate 60 × 60 × 6, Ø30 through-opening, four Ø3.7 holes on a
  31 mm square. Four hex pockets, 5.72 across flats × 3 deep, on the
  motor side.
- **Loose faceplate** — a separate sample of the gearbox joint, for
  checking the interface on its own. It does not stack into the
  assembled fixture.

The steel base plate (14 × 12 × 0.5 in, A36) is proposed as the common
datum for both supports. No finished-plate order is documented, and
6061 aluminum remains a candidate for later fixture parts.

### What changed across the rounds

- The first faceplate opening (Ø24) interfered with the Ø28 hub
  flange. r03 opens it to Ø30 (1 mm nominal radial clearance).
- The stand base opens around the gearbox support (0.75 mm nominal
  separation) instead of overlapping it.
- Gussets moved out of the cheeks so the bracket screws stay
  reachable, and the hub gained full-length neck access channels.
- The gearbox joint is a reversed M3: screw head on the gearbox side,
  nut captured in a hex pocket on the motor side. The r02 rear-nut
  model interfered with the housing; the motor-side capture is sized
  from a measured nut (see below).

### Measurements (digital caliper, Nov 5)

- One bagged black screw from the gearbox bag: 3.0 mm thread, 5.5 mm
  head, 2.9 mm head height, 10.84 mm overall (about 7.9 mm under the
  head). That is an M3x8, not the M4x8 the drawing calls out for the
  output side. The bag holds four.
- One M3 nut from the September hardware bag: 5.42 mm across flats,
  2.3 mm thick. r03 hex pockets are 5.72 mm across flats (0.15 mm
  clearance per flat) × 3 mm deep.
- Reversed-joint stack: 5 mm flange + 2 mm faceplate web + 2.3 mm nut
  = 9.3 mm. M3x8 falls about 1.5 mm short of full nut engagement.
  M3x10 gives 0.7 mm protrusion past the nut and 1 mm nominal rotor
  clearance.
- Tool constraint: a 25 mm straight driver hits the gearbox housing
  at all four screws. A short L-key with its elbow 12 mm beyond the
  seated head cleared a 60° swing at all four screws in the model.

Two small black cylinders from the gearbox bag remain unidentified,
along with one flat metal key.

### Verification record

The r03 run records 115 passing fixture checks and 340 passing
targeted vendor-geometry checks (`verification_r03.json`). Four part
STEPs reimported as valid single solids; all four STL meshes closed
and consistently wound. The checks cover all 13 gearbox solids, the
bracket, and selected motor bodies including rotor and cable geometry.

Physical fit, stub retention, cable routing, and tool access still
need the unpowered print check. PETG parts are for unpowered
dimensional checks only. Never power the PETG hub.

## 2026-11-05 to 2026-11-06 — fabrication

- Slant 3D: original hub (`cad/hub-original/`), PETG black, in
  production.
- Treatstock (SD Printing): r03 set — stand, gearbox support,
  companion hub, loose faceplate — PETG black, in production.
- M3x10 screws: 750-piece stainless assortment (M3x6 through M3x30,
  screws, nuts, washers), ordered Nov 6.
