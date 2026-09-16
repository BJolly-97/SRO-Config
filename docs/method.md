# The method

## Background

In a perfectly random solid solution, the probability of finding a given arrangement of
atoms on a site and its nearest neighbours is fixed by the overall composition. Real
materials deviate from this: certain local arrangements are favoured (ordering) or
avoided (clustering / phase separation).

[P. C. Clapp (1971)](https://doi.org/10.1103/PhysRevB.4.255) formalised this for binary
alloys by enumerating the symmetry-distinct arrangements of a central atom's
nearest-neighbour shell — its **configurations** — and comparing the observed count of
each against the random-solid-solution expectation. The ratio is the **enhancement
factor**, β: `β > 0` means the configuration is over-represented, `β < 0`
under-represented.

## What this tool does

`sro-config` applies that idea to the large-box models fitted by RMCProfile, and lifts
two of Clapp's original restrictions:

- **Any crystal structure**, not just primitive / FCC / BCC — the nearest-neighbour
  shell and its symmetry operations are derived from the input `.cif`.
- **Any number of elements** — an *n*-element system is decomposed into its
  **pseudo-binaries** (each partition of the elements into two groups, e.g. `Fe : Ni`,
  or `Ni-Cr : Co-Fe` for a quaternary), and the binary analysis is run for each.

The pipeline is:

1. **`dict`** — from the `.cif`, enumerate the nearest-neighbour positions, the
   symmetry operations that permute them, and every possible configuration, with its
   multiplicity in a random solid solution.
2. **`config`** — for each atom in the `.rmc6f` box, identify its configuration in every
   pseudo-binary, count them, and compute β against the multiplicities from step 1.
3. **`vis`** — draw individual configurations in 3D to see what a given label means
   physically.

## Reference

> P. C. Clapp, *Atomic Configurations in Binary Alloys*, Physical Review B **4**, 255
> (1971). [doi:10.1103/PhysRevB.4.255](https://doi.org/10.1103/PhysRevB.4.255)
