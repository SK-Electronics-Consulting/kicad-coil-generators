# Coil Generators

## Background

PCB coils are becoming quite common, and defining them can take some time. This plugin is intended to capture useful coil generators of various types.  It is also intended to do enough math under-the-hood to prevent collisions between generated features.  

## Installation

This tool is intended to be used within the KiCAD Footprint Wizard tool. To do
so requires installation into KiCAD.  This is either installing using the Plugin and Content Manager or clone this repo into one of the plugin directories.  (Further details below.)

This tool has been tested with KiCAD 7.0.9.  It might work with other versions
(6.x and 7.0.x), but has not been tested.

### For Linux

1. Clone the Repo into `~/.local/share/kicad/7.0/scripting/plugins/`

OR

(Needs to be tested for accuracy, but this is the method I'm using)

1. Clone the repo into your preferred location.
2. `cd flux-neutral-coil-generator`
3. `ln -s ${PWD}/flux_neutral_coil_generator.py ~/.local/share/kicad/7.0/scripting/plugins/flux_neutral_coil_generator.py`

### For Mac

TODO but should be similar to Linux

### For Windows

1. Clone repo into `{Documents}\KiCad\7.0\scripting`

## Usage

1. Launch by opening KiCAD -> Footprint Editor -> Footprint Wizard (second icon, the one with the red star)
1. If it was installed correctly, it should show up at the end of the list of footprint wizards.
1. Select and click OK.
1. Adjust the parameters as needed.  Please note the limitations below, especially the inner layers not showing up in preview.
1. Export the footprint to the editor. (Last icon in the upper left.)
1. Save this to an appropriate footprint library.  
1. From here, just use this as a footprint for an inductor in KiCAD, as it follows the normal design flow.

## Coil Generator templates

1. `CoilGeneratorID2L:` This coil generator will make a single coil across 2 PCB layers, and will do so starting from a defined inner diameter. It's intended to go around an open hole in the PCB.
1. `CoilGenerator1L1T:` This coil generator will make a simple, single turn coil, terminating in vias.  It's intended to be used with another coil generator, and act as a pickup coil. 

## Limitations

This tool will have several limitations in it's current state.

1. It will not check for manufacturability of the coil.  However, you can do this in PCBNew.
1. It will not check all conditions of if it will make a shape that's not plausible.  Specifically, using a min-radius of 0 will cause issues with the vias.
1. At it's current setup, it will only generate a 2 layer configuration. Using more than 2 layers will probably need a different topology.
1. If setting the layers to an inner layer, the Footprint Wizard will not display correctly.  This is a bug/limitation of KiCAD.  Once it's exported, it will work correctly.  One alternative to this is to generate the shape with F_Cu/B_Cu, and then do a text replacement after the fact.

## To dos

1. TODO: Add the flux neutral coil generator from my other repo.
1. TODO: Add different geometries of coils.
1. TODO: Add an inductance calculator with verification data.
