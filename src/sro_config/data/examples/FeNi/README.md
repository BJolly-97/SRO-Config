# Example: FeNi solid solution

A tiny synthetic Fe/Ni structure (Pm-3m, full cubic point group, Fe and Ni sharing
one disordered sub-lattice). Small enough to run in a second; the same commands work
unchanged on a real 100k-atom RMCProfile box.

- `FeNi.cif` — the crystal structure
- `FeNi_solid_solution.rmc6f` — one large-box configuration

## Run it

From this directory:

```bash
# 1. Build the dictionaries (merge Fe and Ni into one sub-lattice)
sro-config dict --cif FeNi.cif --equivalence 0,1

# 2. Enhancement-factor analysis for sub-lattice 0
sro-config config --dict-dir . --sublattice 0 --rmc6f FeNi_solid_solution.rmc6f

# 3. Visualise a couple of Clapp configurations
sro-config vis --dict-dir . --sublattice 0 --config 1,12
```

Step 2 writes `FeNi_solid_solution_sub0_EF.clapp` (the enhancement factors) and a set
of `*_EF*.png` histograms next to the input. Everything the run generates here is
git-ignored.
