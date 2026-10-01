# Reusable TikZ for the PH 250 lab manual

Every figure is a small standalone `.tex` file in `Figures/` (named
`<chapter>-<description>.tex`) compiled to PDF and pulled into the manual with
`\includegraphics`. This folder holds what those figures share:

* `lab-style.tex` - colours and drawing styles (no other `\input`s)
* `*-pic.tex` - reusable components, each defined as a TikZ `pic`
* shared figures used by more than one chapter (`warning-destroy-arduino`,
  `battery-resistor-circuit`, `two-resistors-in-series`, `ohms-law-graph`,
  `sine-voltage-versus-time`, `multimeter-alternate-model`)

A figure inputs the style file and exactly the component files it uses:

```latex
\documentclass[tikz,border=5pt]{standalone}
\input{Reusable_TikZ/lab-style.tex}
\input{Reusable_TikZ/oscilloscope-pic.tex}
\begin{document}
\begin{tikzpicture}
  \pic (s) {oscilloscope={CH1 2.00V}{}{M 1.00ms}{8}};
\end{tikzpicture}
\end{document}
```

Build: `python Figures/build_figures.py` (out-of-date figures) or `--all`.

## Working with the TikZ editor

The figures are written so the TikZ editor can display and edit them:

* one level of plain `\input{...}` (the editor only loads files the figure
  inputs directly, relative to the figure's folder)
* component settings are pic **arguments**, never `.initial` keys
* no `\newcommand` drawing macros, pgfplots, circuitikz, `\ifx`, `tanh`,
  `\pgfmathtruncatemacro`, or custom `x=`/`y=` axis vectors
* scale a component with `\pic[scale=...]` (add `transform shape` when it has
  text); a scope's `scale` does not reach inside a pic in TeX
* keep TeX math under 16000 (plot in kHz / ms / kohm, not Hz / s / ohm)

Each `*-pic.tex` file is self-contained (it `\providecolor`s its colours), so
it can be opened on its own in the editor to edit the component.

## Components

| pic | file | arguments / key anchors |
|---|---|---|
| `protoboard={rails 0/1}{jumpers 0/1}` | `protoboard-pic.tex` | `-upper-<row>-<col>`, `-lower-...`, `-top-plus-<col>`, `-origin`; `protoboard connections` overlays the metal strips |
| `arduino uno` | `arduino-uno-pic.tex` | `-d0`..`-d13`, `-a0`..`-a5`, `-5v`, `-gnd-digital`, `-usb` |
| `multimeter={reading}{unit}{dial angle}{model 1/2}` | `multimeter-pic.tex` | `-jack-10a/ma/com/vomega`, `-selector`; dial 20 = 10 A, 48 = A, 76 = mA, 132 = DC V, 188 = ohm |
| `oscilloscope={CH1}{CH2}{time}{8/10 divisions}` | `oscilloscope-pic.tex` | `-screen-center`, `-screen-west`, `-ch1`, `-ch2`, `-cal`, knobs and buttons; `scope marker={colour}{n}` |
| `power supply={volts}{amps}` | `power-supply-pic.tex` | `-plus`, `-minus`, `-gnd`, knobs, displays |
| `signal generator={reading}{unit}` | `signal-generator-pic.tex` | `-output`, `-sync`, knobs, buttons |
| `app window={width}{height}{title}{menu}` | `app-window-pic.tex` | `-body-north-west` ... (top-left corner at the origin) |
| `laptop` | `laptop-pic.tex` | `-screen-center`, `-usb` |
| `vertical led=len`, `vertical resistor=len`, `horizontal resistor=len`, `vertical capacitor=len`, `banded resistor={5 colours}`, `alligator clip=colour` | `breadboard-parts-pic.tex` | place at the first hole; `len` in board units |
| `resistor`, `capacitor`, `inductor`, `battery`, `ac source`, `meter=V`, `ground` | `schematic-pic.tex` | 1.2 long along +x, `-left`/`-right`; rotate to stand up |
| `person=colour`, `faucet`, `nozzle`, `water tank`, `turbine`, `pump`, `electron`, `positive charge` | `analogy-pics.tex` | |

Drawing on the oscilloscope screen (units of divisions):

```latex
\begin{scope}[shift={(s-screen-center)},xscale=.4,yscale=.4]  % yscale=.32 for 10 divisions
  \clip (-5,-4) rectangle (5,4);
  \draw[otamber,line width=1.3pt] plot[domain=-5:5,samples=150] (\x,{2*sin(90*\x)});
\end{scope}
```
