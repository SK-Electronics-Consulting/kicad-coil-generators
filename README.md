# Coil Generators

## Background

PCB coils are becoming quite common, and defining them can take some time. This plugin is intended to capture useful coil generators of various types.  It is also intended to do enough math under-the-hood to prevent collisions between generated features.  

## Installation

This tool is intended to be used within the KiCAD Footprint Wizard tool. To do so requires installation into KiCAD.  This is either installing using the Plugin and Content Manager or clone this repo into one of the plugin directories.  (Further details below.)

This tool has been tested with KiCAD 8.0.1.  It might work with other versions (6.x and 7.x), but has not been tested.

### For Linux

1. Clone the Repo into `~/.local/share/kicad/8.0/scripting/plugins/`

### For Mac

TODO but should be similar to Linux

### For Windows

1. Clone repo into `{Documents}\KiCad\8.0\scripting`

## Usage

1. Launch by opening KiCAD -> Footprint Editor -> Footprint Wizard (second icon, the one with the red star)
1. If it was installed correctly, it should show up at the end of the list of footprint wizards.
1. Select and click OK.
1. Adjust the parameters as needed.  Please note the limitations below, especially the inner layers not showing up in preview.
1. Export the footprint to the editor. (Last icon in the upper left.)
1. Save this to an appropriate footprint library.  
1. From here, just use this as a footprint for an inductor in KiCAD, as it follows the normal design flow.

## Coil Generator templates

1. `CoilGeneratorID2L:` This will make a single coil across 2 PCB layers, and will do so starting from a defined inner diameter. It's intended to go around an open hole in the PCB.
1. `CoilGenerator1L1T:` This will make a simple, single turn coil, terminating in vias.  It's intended to be used with another coil generator, and act as a pickup coil.
1. `FluxNeutralCoilGen:` This will make a flux-neutral coil inside of a circular aperture.  The purpose of a flux neutral coil is to cancel out any flux that affects both coils, but will pick up any flux that affects only one.  Use as you see fit.

## Limitations

This tool will have several limitations in it's current state.

1. It will not check for manufacturability of the coil.  However, you can do this in PCBNew.
1. It will not check all conditions of if it will make a shape that's not plausible.  Specifically, using a min-radius of 0 will cause issues with the vias.
1. If setting the layers to an inner layer, the Footprint Wizard will not display correctly.  This is a bug/limitation of KiCAD.  Once it's exported, it will work correctly.  One alternative to this is to generate the shape with F_Cu/B_Cu, and then do a text replacement after the fact.

## Version history

| Version | Description |
| ------- | ----------- |
| 1.0.0   | Initial Version with 2 layer coil and single loop coil |
| 1.1.0   | Add Flux Neutral Coil |
| 1.2.0   | Update to KiCAD 8. Add parameter text into textbox. |

## To dos

1. TODO: Add different geometries of coils. (Rectangular, trapezoidal, wedge of circle)
1. TODO: Add an inductance calculator with verification data.
1. TODO: Add a resistance calculation for Ohms/oz.cu.
1. TODO: Add cutouts to flux neutral and add boolean to enable/disable it.

## Known Issues

1. Flux Neutral coil generator doesn't adjust based on pad size.  
1. In `CoilGeneratorID2L`, somewhere between N=2000 and N=3000, the final coils aren't displayed in the footprint wizard.  Might be a KiCAD bug
