import pcbnew
import FootprintWizardBase
import math
import json
import os

from .PCBTraceComponent import *


class FluxNeutralCoilGen(PCBTraceComponent):
    center_x = 0
    center_y = 0

    json_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "FluxNeutralCoilGen.json"
    )

    GetName = lambda self: "Flux Neutral Coil Generator"
    GetDescription = (
        lambda self: "Generates a flux-neutral coil within a circular aperture."
    )
    GetValue = lambda self: "Flux-Neutral Coil"

    def GenerateParameterList(self):
        # Set some reasonable default values for the parameters
        defaults = {
            "Coil specs": {
                "Turns": 5,
                "Minimum Radius": 1000000,
                "Stub Length": 5000000,
                "First Layer": "F_Cu",
                "Second Layer": "In1_Cu",
            },
            "Install Info": {"Outer Ring radius": 75000000, "Outer Ring gap": 2000000},
            "Fab Specs": {
                "Trace Width": 200000,
                "Trace Spacing": 200000,
                "Via Drill": 254000,
                "Via Annular Ring": 127000,
                "Pad Drill": 500000,
                "Pad Annular Ring": 200000,
            },
        }

        # If this has been run before, load the previous values
        if os.path.exists(self.json_file):
            with open(self.json_file, "r") as f:
                defaults = json.load(f)

        # Info about the coil itself.
        self.AddParam(
            "Coil specs",
            "Turns",
            self.uInteger,
            defaults["Coil specs"]["Turns"],
            min_value=1,
        )
        self.AddParam(
            "Coil specs",
            "Minimum Radius",
            self.uMM,
            pcbnew.ToMM(defaults["Coil specs"]["Minimum Radius"]),
            min_value=0,
        )
        self.AddParam(
            "Coil specs",
            "Stub Length",
            self.uMM,
            pcbnew.ToMM(defaults["Coil specs"]["Stub Length"]),
            min_value=0,
        )
        self.AddParam(
            "Coil specs",
            "First Layer",
            self.uString,
            defaults["Coil specs"]["First Layer"],
            hint="Layer name.  Uses '_' instead of '.'",
        )
        self.AddParam(
            "Coil specs",
            "Second Layer",
            self.uString,
            defaults["Coil specs"]["Second Layer"],
            hint="Layer name.  Uses '_' instead of '.'",
        )

        # Information about where this footprint needs to fit into.
        self.AddParam(
            "Install Info",
            "Outer Ring radius",
            self.uMM,
            pcbnew.ToMM(defaults["Install Info"]["Outer Ring radius"]),
        )
        self.AddParam(
            "Install Info",
            "Outer Ring gap",
            self.uMM,
            pcbnew.ToMM(defaults["Install Info"]["Outer Ring gap"]),
            hint="Gap between the outer loop of this coil and the aperture",
        )

        # Info about the fabrication capabilities
        self.AddParam(
            "Fab Specs",
            "Trace Width",
            self.uMM,
            pcbnew.ToMM(defaults["Fab Specs"]["Trace Width"]),
            min_value=0,
        )
        self.AddParam(
            "Fab Specs",
            "Trace Spacing",
            self.uMM,
            pcbnew.ToMM(defaults["Fab Specs"]["Trace Spacing"]),
            min_value=0,
        )
        self.AddParam(
            "Fab Specs",
            "Via Drill",
            self.uMM,
            pcbnew.ToMM(defaults["Fab Specs"]["Via Drill"]),
            min_value=0,
            hint="Diameter",
        )
        self.AddParam(
            "Fab Specs",
            "Via Annular Ring",
            self.uMM,
            pcbnew.ToMM(defaults["Fab Specs"]["Via Annular Ring"]),
            min_value=0,
            hint="Radius",
        )
        self.AddParam(
            "Fab Specs",
            "Pad Drill",
            self.uMM,
            pcbnew.ToMM(defaults["Fab Specs"]["Pad Drill"]),
            min_value=0,
        )
        self.AddParam(
            "Fab Specs",
            "Pad Annular Ring",
            self.uMM,
            pcbnew.ToMM(defaults["Fab Specs"]["Pad Annular Ring"]),
            min_value=0,
        )

    def CheckParameters(self):
        self.aperture_r = self.parameters["Install Info"]["Outer Ring radius"]
        self.aperture_gap = self.parameters["Install Info"]["Outer Ring gap"]

        self.trace_width = self.parameters["Fab Specs"]["Trace Width"]
        self.trace_space = self.parameters["Fab Specs"]["Trace Spacing"]
        self.via_hole = self.parameters["Fab Specs"]["Via Drill"]
        self.via_ann_ring = self.parameters["Fab Specs"]["Via Annular Ring"]
        self.pad_hole = self.parameters["Fab Specs"]["Pad Drill"]
        self.pad_ann_ring = self.parameters["Fab Specs"]["Pad Annular Ring"]

        self.turns = self.parameters["Coil specs"]["Turns"]
        self.min_radius = self.parameters["Coil specs"]["Minimum Radius"]
        self.stub_length = self.parameters["Coil specs"]["Stub Length"]
        self.first_layer = getattr(pcbnew, self.parameters["Coil specs"]["First Layer"])
        self.second_layer = getattr(
            pcbnew, self.parameters["Coil specs"]["Second Layer"]
        )

        with open(self.json_file, "w") as f:
            json.dump(self.parameters, f, indent=4)

    def BuildThisFootprint(self):
        """Draw the outline circle as reference."""
        self.draw.SetLayer(pcbnew.User_1)
        self.draw.Circle(self.center_x, self.center_y, self.aperture_r)

        self.draw.SetLayer(pcbnew.F_Fab)
        self.draw.Value(0, 0, pcbnew.FromMM(1))
        self.draw.SetLayer(pcbnew.F_SilkS)
        self.draw.Reference(0, 0, pcbnew.FromMM(1))

        """ Calculate several of the internal variables needed. """
        pitch = (
            self.trace_space
            + self.trace_width / 2
            + max(self.trace_width / 2, self.via_hole / 2 + self.via_ann_ring)
        )

        # Pythagorean Theorem to determine via spacing
        aa = (
            self.via_hole / 2
            + self.via_ann_ring
            + self.trace_space
            + self.trace_width / 2
        )
        cc = self.via_ann_ring * 2 + self.via_hole + self.trace_space
        via_gap = math.sqrt(cc * cc - aa * aa)  # units of KiCAD_internal

        pad_d = self.pad_ann_ring * 2 + self.pad_hole
        via_d = self.via_ann_ring * 2 + self.via_hole

        self.draw.SetLineThickness(self.trace_width)

        """ Draw the large curves defining the bulk of the coil"""
        arc_center_x = (
            self.center_x - pitch * (self.turns - 1) / 2 - self.min_radius - via_gap
        )
        arc_center_y = self.center_y
        arc_start_x = arc_center_x
        arc_start_y = (
            arc_center_y
            + self.aperture_r
            - self.aperture_gap
            - pitch * (self.turns - 1) / 2
            - self.min_radius
            - via_gap
        )

        for ii in range(self.turns):
            self.draw.SetLayer(self.first_layer)
            self.draw.Arc(
                arc_center_x,
                arc_center_y,
                arc_start_x,
                arc_start_y - ii * pitch,
                pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T),
            )
            self.draw.SetLayer(self.second_layer)
            self.draw.Arc(
                -arc_center_x,
                -arc_center_y,
                -arc_start_x,
                -arc_start_y + ii * pitch,
                pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T),
            )

        """ 
        Draw the vertical tracks for both layers.  This should be defined as the
          center of the shape, so it's easy to calculate.  There is one track
          which will not be the same, and it's drawn separately. 
        """
        start_x = (self.turns - 1) / 2 * pitch
        line_length = (
            self.center_y
            + self.aperture_r
            - self.aperture_gap
            - pitch * (self.turns - 1) * 1.5
            - self.min_radius * 2
            - via_gap
        )

        self.draw.SetLayer(self.first_layer)
        for ii in range(self.turns - 1):
            self.draw.Line(
                start_x - ii * pitch, line_length, start_x - ii * pitch, -line_length
            )
        self.draw.Line(
            -start_x, line_length, -start_x, -line_length + aa * 2
        )  # Stub to breakout to tap point

        self.draw.SetLayer(self.second_layer)
        for ii in range(self.turns):
            self.draw.Line(
                start_x - ii * pitch, line_length, start_x - ii * pitch, -line_length
            )

        """
        Draw the smaller arcs connecting the large arcs and the vertical tracks.
        The Front layer tracks on top will be off-set because they are the ones
        connecting the coils together.  (The second for statement in this 
        section is the one that does this.)
        """
        small_arc_center_x = (self.turns - 1) / 2 * pitch + self.min_radius
        small_arc_center_y = (
            self.center_y
            + self.aperture_r
            - self.aperture_gap
            - pitch * (self.turns - 1) * 1.5
            - self.min_radius * 2
            - via_gap
        )

        self.draw.SetLayer(self.first_layer)
        for ii in range(self.turns):
            if (ii != 0) or (
                self.min_radius != 0
            ):  # Checking for a radius=0 arc. Might be overkill....
                self.draw.Arc(
                    small_arc_center_x,
                    small_arc_center_y,
                    small_arc_center_x - self.min_radius - ii * pitch,
                    small_arc_center_y,
                    pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T),
                )

        for ii in range(self.turns):
            if ii != 0:  # Checking for a radius=0 arc. Might be overkill....
                self.draw.Arc(
                    -small_arc_center_x + pitch,
                    -small_arc_center_y,
                    -small_arc_center_x + self.min_radius + ii * pitch,
                    -small_arc_center_y,
                    pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T),
                )

        self.draw.SetLayer(self.second_layer)
        for ii in range(self.turns):
            if (ii != 0) or (self.min_radius != 0):
                self.draw.Arc(
                    -small_arc_center_x,
                    small_arc_center_y,
                    -small_arc_center_x + self.min_radius + ii * pitch,
                    small_arc_center_y,
                    pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T),
                )

        for ii in range(self.turns):
            if (ii != 0) or (self.min_radius != 0):
                self.draw.Arc(
                    small_arc_center_x,
                    -small_arc_center_y,
                    small_arc_center_x - self.min_radius - ii * pitch,
                    -small_arc_center_y,
                    pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T),
                )

        """
        Draw Horizontal Lines.  These are needed to give space to the vias for
        stacking.  Otherwise, the coils would need to be further apart. 
        """
        # Draw the simple ones first
        self.draw.SetLayer(self.second_layer)
        for ii in range(self.turns):
            self.draw.Line(
                -arc_start_x,
                -arc_start_y + ii * pitch,
                -arc_start_x - via_gap,
                -arc_start_y + ii * pitch,
            )
        self.draw.SetLayer(self.first_layer)
        for ii in range(1, self.turns):
            self.draw.Line(
                arc_start_x,
                -arc_start_y + ii * pitch,
                arc_start_x + via_gap + pitch,
                -arc_start_y + ii * pitch,
            )

        # Draw alternating Horizontal Lines for Vias
        for ii in range(self.turns):
            if (ii % 2) == 1:
                self.draw.SetLayer(self.first_layer)
            else:
                self.draw.SetLayer(self.second_layer)
            self.draw.Line(
                arc_start_x,
                arc_start_y - ii * pitch,
                arc_start_x + via_gap,
                arc_start_y - ii * pitch,
            )

            if (ii % 2) == 1:
                self.draw.SetLayer(self.second_layer)
            else:
                self.draw.SetLayer(self.first_layer)

            self.draw.Line(
                -arc_start_x,
                arc_start_y - ii * pitch,
                -arc_start_x - via_gap,
                arc_start_y - ii * pitch,
            )

        """
        Draw the stitching vias between the front and back layers
        """
        pad_number = 3

        for ii in range(self.turns):
            if (ii % 2) == 1:
                offset = via_gap
            else:
                offset = 0
            pos = pcbnew.VECTOR2I(
                int(arc_start_x + offset), int(arc_start_y - ii * pitch)
            )
            self.PlacePad(pad_number, pos, via_d, self.via_hole, via=True)

            pos = pcbnew.VECTOR2I(
                int(-arc_start_x - offset), int(arc_start_y - ii * pitch)
            )
            self.PlacePad(pad_number, pos, via_d, self.via_hole, via=True)

        """
        Draw the tap points from the coil.  
        
        The Front layer is easy.  The Back layer requres a little bit of work
        and a via to get out.  
        """
        # Draw arc and trace from outer coil
        self.draw.SetLayer(self.first_layer)
        self.draw.Arc(
            arc_center_x,
            -arc_start_y - aa,
            arc_center_x,
            -arc_start_y,
            pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T),
        )
        self.draw.Line(
            arc_center_x + aa,
            -arc_start_y - aa,
            arc_center_x + aa,
            -arc_start_y - aa - self.stub_length,
        )

        # Add Pad for one side of the coil
        pos = pcbnew.VECTOR2I(
            int(arc_center_x + aa), int(-arc_start_y - aa - self.stub_length)
        )
        # self.make_pad(pos, 1)
        self.PlacePad(1, pos, pad_d, self.pad_hole)

        # Diagonal track to get to via
        self.draw.Line(
            -start_x, -line_length + aa * 2, -start_x - aa, -line_length + aa
        )

        # Add Via
        pos = pcbnew.VECTOR2I(int(-start_x - aa), int(-line_length + aa))
        self.PlacePad(pad_number, pos, via_d, self.via_hole, via=True)

        # Vertical track to get under the coils.
        self.draw.SetLayer(self.second_layer)
        self.draw.Line(
            -start_x - aa,
            -line_length + aa,
            -start_x - aa,
            -line_length - aa - (self.turns - 1) * pitch,  # - self.stub_length,
        )

        # Jogging right to clear space for Vias
        self.draw.Line(
            -start_x - aa,
            -line_length - aa - (self.turns - 1) * pitch,  # - self.stub_length,
            -start_x - aa + self.min_radius,
            -line_length - aa - (self.turns - 1) * pitch - self.min_radius,
        )

        # Add Via
        pos = pcbnew.VECTOR2I(
            int(-start_x - aa + self.min_radius),
            int(-line_length - aa - (self.turns - 1) * pitch - self.min_radius),
        )
        self.PlacePad(pad_number, pos, via_d, self.via_hole, via=True)

        # Drawing stub section
        self.draw.SetLayer(self.first_layer)
        self.draw.Line(
            -start_x - aa + self.min_radius,
            -line_length - aa - (self.turns - 1) * pitch - self.min_radius,
            -start_x - aa + self.min_radius,
            -arc_start_y - aa - self.stub_length,
        )

        # Add pad for other side of the coil
        pos = pcbnew.VECTOR2I(
            int(-start_x - aa + self.min_radius),
            int(-arc_start_y - aa - self.stub_length),
        )
        self.PlacePad(2, pos, pad_d, self.pad_hole)

        """
        Add Net Tie Group to the footprint. This allows the DRC to understand 
        that the shorting traces are OK for this component
        """
        self.GenerateNetTiePadGroup()

        """
        Capture the parameters in the Fab layer
        """
        fab_text_s = (
            f"Flux Neutral Coil\n"
            f"Outer Diameter: {self.aperture_r/1e6}\n"
            f"Outer Ring Gap: {self.aperture_gap/1e6}\n"
            f"Turns: {self.turns}\n"
            f"Min Radius: {self.min_radius/1e6}\n"
            f'Layers (Start->Finish): {self.parameters["Coil specs"]["First Layer"]}->{self.parameters["Coil specs"]["Second Layer"]}\n'
            f"Trace Width/space: {self.trace_width/1e6}/{self.trace_space/1e6}\n"
            f"Via Drill/annular ring: {self.via_hole/1e6}/{self.via_ann_ring/1e6}\n"
            f"Pad Drill/annular ring: {self.pad_hole/1e6}/{self.pad_ann_ring/1e6}\n"
            f"Stub Length: {self.stub_length/1e6}\n"
        )
        self.DrawText(fab_text_s, pcbnew.User_2)
