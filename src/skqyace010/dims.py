"""Dimensions of the Alps Alpine SKQYACE010 TACT switch, in millimetres.

Single source of every number used by the model. Sources:

* ``# datasheet`` -- dimensioned on the ALPS SKQY catalogue page 212,
  *TACT Switch SKQY 6.1 x 3.7 mm (Surface Mount Type)*, "Dimensions"
  drawing, published on the ALPS product page
  https://tech.alpsalpine.com/e/products/detail/SKQYACE010/ (the PDF is not
  part of this repository).
* ``# estimate`` -- not dimensioned there. Measured off that drawing
  rasterised at 800 dpi; the scale is calibrated on the 6.1 body width
  (653 px, i.e. 107.0 px/mm) and cross-checked on the side-view 2.5 height
  (272 px, i.e. 108.8 px/mm, +1.6 %). Pixel spans are given in each comment.

No value comes from the vendor 3D model.

Coordinate frame (KiCad): origin at the footprint origin (midpoint of pads
1 and 2), +X towards pad 2, +Z out of the board, seating plane at Z = 0.
"""

# --- Datasheet ------------------------------------------------------------

BODY_W = 6.1  # datasheet: body width (X)
BODY_D = 3.7  # datasheet: body depth (Y)
TERMINAL_SPAN = 6.8  # datasheet: terminal tip to tip (X)
TERMINAL_W = 0.8  # datasheet: terminal width (Y)
HEIGHT = 2.5  # datasheet: seating plane to stem top (Z)
STEM_LOBE_W = 2.6  # datasheet: stem width across its side lobes (X)
STEM_LOBE_H = 1.2  # datasheet: stem lobe height (Y)
STEM_D = 1.8  # datasheet: stem centre diameter

# Footprint lands (cornet_ec:SKQYACE010, from the same drawing): 2.0 x 1.0 at
# X = +-3.0. Used only by the tests to check that the terminal feet land on them.
PAD_X = 3.0  # datasheet: land centre (8 / 4 mm outer / inner)
PAD_L = 2.0  # datasheet: land length (X)
PAD_W = 1.0  # datasheet: land width (Y)

# --- Estimates ------------------------------------------------------------

BODY_H = 1.47  # estimate: body top 160 px above seating plane (side view)
BODY_CHAMFER = 0.4  # estimate: top-view corner break 46 x 45 px

TIER_W = 4.1  # estimate: raised tier 442 px wide (top and side view)
TIER_D = 2.3  # estimate: raised tier 245 px deep (top view)
TIER_R = 0.4  # estimate: raised tier corner radius ~45 px (top view)
TIER_TOP = 2.07  # estimate: tier top 225 px above seating plane (side view)

STEM_LOBE_R = 0.3  # estimate: lobe end corner radius ~30 px (top view)

TERMINAL_T = 0.2  # estimate: terminal sheet thickness ~20-25 px (side view)
TERMINAL_FOOT_X = 2.7  # estimate: foot starts 38 px inside the body edge
TERMINAL_LEAF_H = 1.0  # estimate: leaf tip 110 px above seating plane
TERMINAL_LEAF_BASE_X = 3.0  # estimate: leaf leaves the body edge at ~3.0

# Metal cover and plastic base. Side-view Z scale is 110.2 px/mm (seating
# plane at row 349.5, stem top at row 74); X scale 107.0 px/mm; top-view Y
# scale 109.7 px/mm (3.7 = 406 px). Centre line at column 636.
COVER_X = 2.75  # estimate: top-view cover end lines at columns 339.5 / 928.5
COVER_T = 0.10  # estimate: sheet thickness, not drawn (typical for this size)
SKIRT_X = 2.62  # estimate: side-view skirt end lines at columns 355.5 / 916.5
SKIRT_BOTTOM = 0.18  # estimate: side-view skirt bottom edge at row 329.5
NOTCH_W = 2.42  # estimate: side-view notch sides at columns 506.5 / 765.5
NOTCH_TOP = 0.785  # estimate: side-view notch top edge at row 263
NOTCH_R = 0.10  # estimate: notch top corner radius (~10 px)
LATCH_W = 0.13  # estimate: side-view latch tab, columns 341.5-355.5
LATCH_H = 0.18  # estimate: side-view latch tab, rows 190-210
TIER_EDGE_R = 0.10  # estimate: pressed-edge round on the tier top (~11 px)
STEM_CLEAR = 0.05  # estimate: gap around the stem in the tier opening
END_SLOT_W = 1.5  # estimate: top-view end slot edges at rows 621.5 / 785.5
END_SLOT_D = 0.3  # estimate: top-view end slot depth, columns 309-340

# --- Derived --------------------------------------------------------------

TERMINAL_TIP_X = TERMINAL_SPAN / 2  # 3.4
