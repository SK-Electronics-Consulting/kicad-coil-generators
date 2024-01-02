import pcbnew
import FootprintWizardBase
import math


class FluxNeutralCoilGen(FootprintWizardBase.FootprintWizard):
    GetName = lambda self: "Flux Neutral Coil Generator"
    GetDescription = (
        lambda self: "Generates a flux-neutral coil within a circular aperture."
    )
    GetValue = lambda self: "Flux-Neutral Coil"

    center_x = 0
    center_y = 0

    def GenerateParameterList(self):
        # Info about the coil itself.
        self.AddParam("Coil specs", "Turns", self.uInteger, 5, min_value=1)
        self.AddParam("Coil specs", "Minimum Radius", self.uMM, 1, min_value=0)
        self.AddParam("Coil specs", "Stub Length", self.uMM, 5, min_value=0)
        self.AddParam(
            "Coil specs",
            "First Layer",
            self.uString,
            "F_Cu",
            hint="Layer name.  Uses '_' instead of '.'",
        )
        self.AddParam(
            "Coil specs",
            "Second Layer",
            self.uString,
            "In1_Cu",
            hint="Layer name.  Uses '_' instead of '.'",
        )

        # Information about where this footprint needs to fit into.
        self.AddParam("Install Info", "Outer Ring radius", self.uMM, 75)
        self.AddParam(
            "Install Info",
            "Outer Ring gap",
            self.uMM,
            2,
            hint="Gap between the outer loop of this coil and the aperture",
        )

        # Info about the fabrication capabilities
        self.AddParam("Fab Specs", "Trace Width", self.uMM, 0.2, min_value=0)
        self.AddParam("Fab Specs", "Trace Spacing", self.uMM, 0.2, min_value=0)
        self.AddParam("Fab Specs", "Via Drill", self.uMM, 0.254, min_value=0)
        self.AddParam("Fab Specs", "Via Annular Ring", self.uMM, 0.127, min_value=0)
        self.AddParam("Fab Specs", "Pad Drill", self.uMM, 0.5, min_value=0)
        self.AddParam("Fab Specs", "Pad Annular Ring", self.uMM, 0.2, min_value=0)

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
        via_d = self.via_ann_ring * 2 + self.via_hole
        pad_number = 3
        pad = pcbnew.PAD(self.module)
        pad.SetSize(pcbnew.VECTOR2I(via_d, via_d))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        pad.SetDrillSize(pcbnew.VECTOR2I(self.via_hole, self.via_hole))

        for ii in range(self.turns):
            if (ii % 2) == 1:
                offset = via_gap
            else:
                offset = 0
            pos = pcbnew.VECTOR2I(
                int(arc_start_x + offset), int(arc_start_y - ii * pitch)
            )
            pad.SetPosition(pos)
            pad.SetPos0(pos)
            pad.SetNumber(pad_number)
            pad.SetName(str(pad_number))
            self.module.Add(pad)
            pad = (
                pad.Duplicate()
            )  # needed because otherwise you keep editing the same object.

            pos = pcbnew.VECTOR2I(
                int(-arc_start_x - offset), int(arc_start_y - ii * pitch)
            )
            pad.SetPosition(pos)
            pad.SetPos0(pos)
            pad.SetNumber(pad_number)
            pad.SetName(str(pad_number))
            self.module.Add(pad)
            pad = pad.Duplicate()

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
        pad = pcbnew.PAD(self.module)
        pad.SetSize(
            pcbnew.VECTOR2I(
                self.pad_ann_ring + self.pad_hole, self.pad_ann_ring + self.pad_hole
            )
        )
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pad.PTHMask())
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetDrillSize(pcbnew.VECTOR2I(self.pad_hole, self.pad_hole))
        pad.SetPos0(pos)
        pad.SetPosition(pos)
        pad.SetNumber(1)
        pad.SetName("1")
        pad.SetLayer(self.first_layer)
        self.module.Add(pad)

        # Diagonal track to get to via
        self.draw.Line(
            -start_x, -line_length + aa * 2, -start_x - aa, -line_length + aa
        )
        # Add Via
        pos = pcbnew.VECTOR2I(int(-start_x - aa), int(-line_length + aa))
        pad = pcbnew.PAD(self.module)
        pad.SetSize(pcbnew.VECTOR2I(via_d, via_d))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        pad.SetDrillSize(pcbnew.VECTOR2I(self.via_hole, self.via_hole))
        pad.SetNumber(pad_number)
        pad.SetName(str(pad_number))
        pad_number += 1
        pad.SetPos0(pos)
        pad.SetPosition(pos)
        self.module.Add(pad)

        # Vertical track to get under the coils.
        self.draw.SetLayer(self.second_layer)
        self.draw.Line(
            -start_x - aa,
            -line_length + aa,
            -start_x - aa,
            -line_length - aa - (self.turns - 1) * pitch - self.stub_length,
        )

        # Jogging right to clear space for Vias
        self.draw.Line(
            -start_x - aa,
            -line_length - aa - (self.turns - 1) * pitch - self.stub_length,
            -start_x - aa + self.min_radius,
            -line_length
            - aa
            - (self.turns - 1) * pitch
            - self.stub_length
            - self.min_radius,
        )

        # Add pad for other side of the coil
        pos = pcbnew.VECTOR2I(
            int(-start_x - aa + self.min_radius),
            int(-arc_start_y - aa - self.stub_length),
        )
        pad = pcbnew.PAD(self.module)
        pad.SetSize(
            pcbnew.VECTOR2I(
                self.pad_ann_ring + self.pad_hole, self.pad_ann_ring + self.pad_hole
            )
        )
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pad.PTHMask())
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetDrillSize(pcbnew.VECTOR2I(self.pad_hole, self.pad_hole))
        pad.SetPos0(pos)
        pad.SetPosition(pos)
        pad.SetNumber(2)
        pad.SetName("2")
        self.module.Add(pad)

        """
        Add Net Tie Group to the footprint. This allows the DRC to understand 
        that the shorting traces are OK for this component
        """
        self.module.AddNetTiePadGroup("1,2,3")
