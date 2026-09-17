# Public Data Analysis Tool: Quick Guide

`yield.py` reads the public data tables and produce tables or plots. It requires Python 3, NumPy, and Matplotlib. The examples below assume that `python` runs Python 3.

Use `--help` to display the available options. Running a script without options also displays its help message.

```bash
python yield.py --help
```

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

Output tables contain the nuclide or group identifiers, ejecta mass, `X`, and `Y`. For `isobar` and `element`, `Y` is the sum of the individual nuclide abundances. 

By default, plots include the solar r-process abundance distribution. Place `solar-r-isotope-prantzos.dat` in the same directory as `yield.py`. The solar distribution is scaled to match the input at `A=151` for `isotope` and `isobar`, or at `Z=63` for `element`. Both datasets must have a positive abundance at the normalization point.

```bash
# Omit the solar distribution; no solar data file is needed
python yield.py --plot all --solar no

# Normalize the solar distribution at A=130
python yield.py --plot isobar --solar 130
```
