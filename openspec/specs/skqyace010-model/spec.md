# skqyace010-model Specification

## Purpose

Provide a licence-clean, datasheet-derived 3D model of the Alps Alpine SKQYACE010 TACT switch. It replaces the vendor STEP in the KiCad 3D view and can be redistributed with the project.

## Requirements

### Requirement: Geometry derived only from the public datasheet

The model SHALL be drawn only from dimensions in the public ALPS SKQY datasheet: the catalogue page *TACT Switch™ SKQY 6.1 × 3.7 mm (Surface Mount Type)*, page 212, "Dimensions" drawing, published from the ALPS product page (`https://tech.alpsalpine.com/e/products/detail/SKQYACE010/`). No vertices, faces or measurements SHALL be copied or derived from the vendor 3D model (the ALPS "3D CAD" STEP download). Any dimension the datasheet does not give SHALL be marked as an estimate, both in the source and in the README. Product photos (for example LCSC C262417) MAY be used as a visual reference for colours and for which features exist. They SHALL NOT be a source of any dimension, and they SHALL NOT be committed.

Copies of the datasheet PDF and the vendor STEP MAY be kept in a machine-local directory that is excluded from version control. No committed source, test, build script, doc or main spec SHALL reference that directory or any file in it; the only file that SHALL name it is the ignore rule that excludes it. Any tool that needs to read the datasheet or the vendor STEP SHALL take the file path as an explicit parameter and SHALL NOT assume a default location in the repository.

#### Scenario: Every dimension is traceable

- **WHEN** a reviewer reads the model source
- **THEN** each dimension parameter is either labelled with the datasheet value it implements (e.g. `6.1` body width) or labelled `estimate` with a note on how it was measured from the datasheet drawing

#### Scenario: No vendor data in the repository

- **WHEN** the committed tree is inspected (`git ls-files`)
- **THEN** it contains no datasheet PDF, no vendor STEP, no product photo, and no file derived from the vendor STEP

#### Scenario: No reference to the machine-local datasheet directory

- **WHEN** the test suite runs on a clone that has no machine-local datasheet directory
- **THEN** the build and every test pass, and a test confirms that no committed file except the ignore rule references that directory

#### Scenario: Datasheet path is a parameter

- **WHEN** a tool is added that reads the datasheet or the vendor STEP
- **THEN** it receives the file path as an explicit argument and fails with a clear error if the path is missing, instead of falling back to a path inside the repository

### Requirement: Datasheet-dimensioned envelope

The model SHALL match the datasheet's dimensioned features to within ±0.05 mm:

| Feature | Value (mm) |
|:---|:---|
| Body width (X) | 6.1 |
| Body depth (Y) | 3.7 |
| Terminal tip-to-tip (X) | 6.8 |
| Terminal width (Y) | 0.8 |
| Overall height, seating plane to stem top (Z) | 2.5 |
| Stem overall width across its side lobes (X) | 2.6 |
| Stem lobe height (Y) | 1.2 |
| Stem central diameter | 1.8 |

Note: on close reading of the drawing, 2.6 and 1.2 describe the lens-shaped stem (a Ø1.8 circle with side lobes), not the raised stem housing. The side view confirms this: the topmost step is 2.6 wide.

The ground-terminal features marked ※ in the datasheet (0.5, 1.85, 2.7, 4.7, 5.3 mm) SHALL NOT be modelled, because SKQYACE010 has no ground terminal.

#### Scenario: Bounding box matches the datasheet

- **WHEN** the bounding box of the exported model is measured
- **THEN** X spans 6.8 ± 0.05 mm, Y spans 3.7 ± 0.05 mm, and Z runs from 0 to 2.5 ± 0.05 mm

#### Scenario: Stem is centred and correctly sized

- **WHEN** the stem solid is measured
- **THEN** it is centred on the Z axis, spans 2.6 ± 0.05 mm in X and 1.8 ± 0.05 mm in Y (the central Ø1.8 circle), and its top face is at Z = 2.5 ± 0.05 mm

### Requirement: KiCad-native coordinate frame

The model SHALL be in millimetres with +Z pointing out of the PCB. The origin SHALL be at the footprint origin of `cornet_ec:SKQYACE010`, i.e. the midpoint between pad 1 (X = −3.0) and pad 2 (X = +3.0). The lowest point of the terminals SHALL lie on Z = 0. The terminals SHALL run along ±X to match the footprint lands.

#### Scenario: Drop-in placement with identity transform

- **WHEN** the STEP model is assigned to `cornet_ec:SKQYACE010` with offset `(0,0,0)`, scale `(1,1,1)` and rotate `(0,0,0)`
- **THEN** the KiCad 3D viewer shows the switch sitting on the board surface, with each terminal foot inside its 2.0 × 1.0 mm land and the stem centred on the footprint origin

### Requirement: Simplified, part-separated, coloured representation

The model SHALL contain exactly these parts, each a separate closed solid: the plastic base, the metal cover, the stem, terminal 1 and terminal 2. The cover SHALL include the features the datasheet drawing shows:

- a top plate that ends short of the body's X ends, leaving the base visible at both ends;
- the pressed raised tier, with an opening through which the stem protrudes;
- skirts down the ±Y faces, each with a notch at the bottom centre.

Details that cannot be seen at KiCad 3D-view scale SHALL be omitted: inner contacts, snap dome, moulding draft, stem texture, cover dimple and underside markings. Round features SHALL be true circular or cylindrical surfaces, not faceted. In the STEP output each part SHALL carry a colour: base black, cover stainless-steel grey, stem brown, terminals gold. The model SHALL therefore have four distinct colours.

#### Scenario: Parts are distinguishable in the 3D viewer

- **WHEN** the STEP is opened in the KiCad 3D viewer or another STEP viewer
- **THEN** the base, cover, stem and terminals each show in their own colour and are separate solids

#### Scenario: Stem has true curved faces

- **WHEN** the STEP is inspected
- **THEN** the stem's Ø1.8 side faces are cylindrical surfaces, not sets of planar facets

#### Scenario: Plastic base visible at the ends

- **WHEN** the model is viewed from above
- **THEN** the cover's top plate ends short of the 6.1 mm body length on both X ends, and the black base is visible between the cover edge and the body end

#### Scenario: Skirt notch present

- **WHEN** the cover is sectioned or viewed along Y
- **THEN** each ±Y skirt has a notch centred on X = 0 at its bottom edge, so the skirt does not reach the seating plane there

#### Scenario: Stem passes through the cover

- **WHEN** the stem and cover solids are compared
- **THEN** the stem rises above the cover's tier top and does not intersect the cover solid; the tier has an opening around it

### Requirement: Provenance and licence documentation

The repository SHALL include a README that states the model's provenance (drawn from the datasheet, no vendor geometry used), its licence and the KiCad usage transform. The README SHALL also give the dimension table, showing which values come from the datasheet and which are estimates. It SHALL state that colours and appearance follow product photos, which are not part of the repository, while every dimension comes from the datasheet.

#### Scenario: Consumer can verify licence cleanliness

- **WHEN** a downstream user reads the README
- **THEN** they find the source document, a statement that no vendor 3D data was used, a statement that product photos informed colour and appearance only and are not included, the licence, and the footprint transform `(0,0,0)/(1,1,1)/(0,0,0)`
