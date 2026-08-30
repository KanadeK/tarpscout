# Differentiation research

Research was performed on 2026-08-27 before implementation. It compared the
large local OSS portfolio, prior discussed concepts, several exact GitHub
queries, and representative adjacent tools. Search results and popularity can
change; this note records the selection evidence, not a permanent claim that no
similar project can ever exist.

## Concepts rejected before selection

- Bicycle spoke-tension planning was rejected after finding established tools
  such as [bike-wheel-calc](https://github.com/dashdotrobot/bike-wheel-calc),
  Wheelwright, and Park Tool's wheel-tension workflow.
- Trailer load/balance simulation was rejected because existing simulators
  already cover weight placement and because incorrect guidance carries a high
  road-safety cost.
- Gel/blot layout, seed image analysis, crop rotation, foster management, and
  general tarp-area calculators were rejected after finding close tools or an
  insufficiently distinct executable core.

The local workspace was also checked against already built or discussed
projects, including SofaPilot (furniture route planning), MeshReady (screen-print
capacity), BalloonOrder (comic reading order), multi-dish scheduling, camera and
projection planning, sewing/weaving, and numerous developer diagnostics.
TarpScout does not reuse those domains or algorithms.

## GitHub query evidence

The exact repository queries
[`"tarp planner"`](https://github.com/search?q=%22tarp+planner%22&type=repositories),
[`"tarp pitch calculator"`](https://github.com/search?q=%22tarp+pitch+calculator%22&type=repositories),
[`"camping tarp anchor planner"`](https://github.com/search?q=%22camping+tarp+anchor+planner%22&type=repositories),
and
[`"tarp site solver"`](https://github.com/search?q=%22tarp+site+solver%22&type=repositories)
returned no direct repository match at research time. The related
[hammock-calculator](https://github.com/midking/hammock-calculator) addresses
hammock hang geometry rather than a measured tarp site.

## Material distinction

| Adjacent category | Typical input/output | TarpScout difference |
|---|---|---|
| Tarp size/area formula | Width, length, coverage estimate | Uses actual support coordinates, heights, footprints, and allowed stake ground |
| Hammock hang calculator | Tree distance, suspension angle, hang height | Searches A-frame/lean-to tarp projections and four independent hard-constraint classes |
| Drawing/CAD tool | User manually places lines and shapes | Produces feasible coordinates, exact cord assignment, ranking, and no-solution evidence |
| Packing checklist | Inventory presence | Uses each reusable cord segment as a length-constrained resource |

The executable core is therefore not “a tarp-themed interface.” A successful
plan must simultaneously pass support-span/height geometry, roof slope,
footprint containment, polygonal stake placement, circular keep-out collision,
and exact cord assignment. A blocked plan returns stable counted causes.

## Discovery potential, without a star promise

No design can guarantee GitHub stars or traffic. TarpScout improves its chance
of being useful and shareable through a specific outdoor problem, a zero-account
offline CLI, editable examples, inspectable SVG/HTML evidence, deterministic
automation, Windows/Linux CI, and a wheel plus demo bundle. Popularity remains a
user/community outcome, not an acceptance criterion the code can honestly
claim.
