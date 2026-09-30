# Public Data Analysis Tools: Quick Guide

`yield.py`, `ejecta.py`, and `qdot.py` read the public data tables and produce tables or plots. They require Python 3, NumPy, and Matplotlib. The examples below assume that `python` runs Python 3.

## Common usage

| Script | Purpose | Default input |
|---|---|---|
| `yield.py` | Isotopic, isobaric, and elemental abundances | `yield.dat` |
| `ejecta.py` | Electron fraction, entropy, and velocity distributions | `ejecta.dat` |
| `qdot.py` | Time evolution of heating rates and elemental mass fractions | `qdot.dat` |

By default, input files are read from the current working directory. Use `--input` to select another file.

```bash
python yield.py --input yield_100s.dat --plot isobar
```

Tables are saved as `.dat` files and plots as `.pdf` files in the current working directory. Use `--output_dir` to choose another output directory.

```bash
python ejecta.py --plot ye --output_dir figures
```

Each output filename includes the full input filename with its final extension removed. This rule also applies to the default input files.

Use `--help` to display the available options. Running a script without options also displays its help message.

```bash
python yield.py --help
python ejecta.py --help
python qdot.py --help
```

## yield.py: Nucleosynthesis abundances

The input is a text file containing `Z A M_ej/M_sun` for each nuclide, where `Z` is the atomic number and `A` is the mass number. The script normalizes the nuclide masses by their total to calculate mass fractions `X` and abundances `Y`. For each nuclide, `Y = X/A`.

| Selection | Quantity |
|---|---|
| `isotope` | Individual nuclides: `X(Z,A)` |
| `isobar` | Sum over nuclides with the same mass number: `X(A)` |
| `element` | Sum over nuclides with the same atomic number: `X(Z)` |
| `all` | All three selections |

```bash
# Write an isotope table
python yield.py --table isotope

# Plot mass fractions as a function of mass number
python yield.py --plot isobar

# Write all tables and plots
python yield.py --table all --plot all

# Print the total nuclide mass in the input, in solar masses
python yield.py --mass
```

Output tables contain the nuclide or group identifiers, ejecta mass, `X`, and `Y`. For `isobar` and `element`, `Y` is the sum of the individual nuclide abundances. Plots show mass fractions on a logarithmic vertical axis spanning `1e-6` to `1`.

By default, plots include the solar r-process abundance distribution. Place `solar-r-isotope-prantzos.dat` in the same directory as `yield.py`. The solar distribution is scaled to match the input at `A=151` for `isotope` and `isobar`, or at `Z=63` for `element`. Both datasets must have a positive abundance at the normalization point.

```bash
# Omit the solar distribution; no solar data file is needed
python yield.py --plot all --solar no

# Normalize the solar distribution at A=130
python yield.py --plot isobar --solar 130
```

For input `yield.dat`, output filenames include `isotope_yield.dat` and `isobar_yield.pdf`. For input `yield_100s.dat`, the corresponding isobar plot is `isobar_yield_100s.pdf`.

## ejecta.py: Ejecta distributions

The input columns are `ID M_ej/M_sun Ye_5GK S_5GK/k_B v/c`. The electron fraction `Ye` and entropy are evaluated at a temperature of 5 GK. The velocity is the final radial velocity divided by the speed of light. 

| Selection | Quantity | Bin width |
|---|---|---|
| `ye` | Electron fraction `Ye` | `0.01` |
| `entropy` | Entropy `S/k_B` | `0.1` in `log10(S/k_B)` |
| `velocity` | Velocity `v/c` | `0.01` |

```bash
# Write an electron-fraction table and a 1D histogram
python ejecta.py --table ye --plot ye

# Plot a 2D distribution: electron fraction on x, entropy on y
python ejecta.py --plot ye entropy

# Write all three tables and all six plots (three 1D and three 2D)
python ejecta.py --table all --plot all

# Print the total mass of the selected rows, in solar masses
python ejecta.py --mass
```

Passing two quantities to `--plot` produces one 2D plot, with the quantities assigned to the horizontal and vertical axes in the specified order.

Tables contain the bin center and the mass in that bin, in solar masses. Entropy tables report bin centers as `log10(S/k_B)`. Electron-fraction and velocity bin centers are `0.00, 0.01, ...`; logarithmic entropy bin centers are `..., -0.1, 0.0, 0.1, ...`.

Plots show the mass in each bin divided by the total mass of the selected rows. The vertical axis of a 1D plot and the color scale of a 2D plot are logarithmic. Entropy axes are also logarithmic; entropy distributions use rows with positive entropy.

For input `ejecta.dat`, output filenames include `ye_ejecta.dat`, `ye_ejecta.pdf`, and `ye_entropy_ejecta.pdf`.

## qdot.py: Heating rates and elemental evolution

The input has 118 columns: time in days in column 1, total heating rate in column 2, `gamma, electron, neutrino, fission, alpha` in columns 3–7, and `X(Z)` for `Z=0,...,110` in columns 8–118. Heating rates are in `erg/g/s`.

```bash
# Plot the total heating rate and all five components together
python qdot.py --plot qdot

# Plot the mass fraction for Z=38
python qdot.py --plot element 38

# Plot Z=38, 39, and 40 together
python qdot.py --plot element 38-40

# Plot Z=38 and 56 together
python qdot.py --plot element 38 56

# Create separate heating-rate and elemental plots in one invocation
python qdot.py --plot qdot --plot element 38 56
```

Ranges and individual values can be combined, for example `--plot element 38-40 56`. Allowed atomic numbers are `0` through `110`.

Both axes are logarithmic. The default time range is `1e-5` to `1000` days. Vertical limits are automatic for heating rates and `1e-6` to `1` for `X(Z)`.

```bash
# Change the time range and vertical limits
python qdot.py --plot element 38 --tmin 0.01 --tmax 100 --ymin 1e-8 --ymax 1

# Omit the reference curve from the heating-rate plot
python qdot.py --plot qdot --no_ref
```

Heating-rate plots include the reference curve `2e10 × (t/day)^(-1.3) erg/g/s` by default. When multiple `--plot` options are used, the specified time range and vertical limits apply to all plots.

| Input file | Selection | Output file |
|---|---|---|
| `qdot.dat` | `--plot qdot` | `rate_qdot.pdf` |
| `qdot.dat` | `--plot element 38-40` | `element_38-40_qdot.pdf` |
| `qdot.dat` | `--plot element 38 56` | `element_38_56_qdot.pdf` |
| `qdot_mhd_nsns_i.dat` | `--plot qdot` | `rate_qdot_mhd_nsns_i.pdf` |
| `qdot_mhd_nsns_i.dat` | `--plot element 38` | `element_38_qdot_mhd_nsns_i.pdf` |
