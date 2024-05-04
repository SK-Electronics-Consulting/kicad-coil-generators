import pcbnew
import FootprintWizardBase
import math


class CoilGeneratorID2L(FootprintWizardBase.FootprintWizard):
    center_x = 0
    center_y = 0

    GetName = lambda self: "Coil Generator from ID"
    GetDescription = lambda self: "Generates a coil around a circular aperture."
    GetValue = lambda self: "Coil based on ID"

    def GenerateParameterList(self):
        # Info about the coil itself.
        self.AddParam("Coil specs", "Total Turns", self.uInteger, 15, min_value=1)
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
            "B_Cu",  # "In1_Cu",
            hint="Layer name.  Uses '_' instead of '.'",
        )
        self.AddParam(
            "Coil specs", "Direction", self.uBool, True, hint="Unused for now"
        )

        # Information about where this footprint needs to fit into.
        self.AddParam("Install Info", "Inside Diameter, Radius", self.uMM, 30)
        self.AddParam(
            "Install Info",
            "Inner Ring gap",
            self.uMM,
            0.5,
            hint="Gap between the innermost loop of this coil and the aperture",
        )

        # Info about the fabrication capabilities
        self.AddParam("Fab Specs", "Trace Width", self.uMM, 0.2, min_value=0)
        self.AddParam("Fab Specs", "Trace Spacing", self.uMM, 0.2, min_value=0)
        self.AddParam(
            "Fab Specs", "Via Drill", self.uMM, 0.3, min_value=0, hint="Diameter"
        )
        self.AddParam(
            "Fab Specs", "Via Annular Ring", self.uMM, 0.15, min_value=0, hint="Radius"
        )
        self.AddParam("Fab Specs", "Pad Drill", self.uMM, 0.5, min_value=0)
        self.AddParam("Fab Specs", "Pad Annular Ring", self.uMM, 0.2, min_value=0)

    def CheckParameters(self):
        self.aperture_r = self.parameters["Install Info"]["Inside Diameter, Radius"]
        self.aperture_gap = self.parameters["Install Info"]["Inner Ring gap"]

        self.trace_width = self.parameters["Fab Specs"]["Trace Width"]
        self.trace_space = self.parameters["Fab Specs"]["Trace Spacing"]
        self.via_hole = self.parameters["Fab Specs"]["Via Drill"]
        self.via_ann_ring = self.parameters["Fab Specs"]["Via Annular Ring"]
        self.pad_hole = self.parameters["Fab Specs"]["Pad Drill"]
        self.pad_ann_ring = self.parameters["Fab Specs"]["Pad Annular Ring"]

        self.turns = self.parameters["Coil specs"]["Total Turns"]
        self.first_layer = getattr(pcbnew, self.parameters["Coil specs"]["First Layer"])
        self.second_layer = getattr(
            pcbnew, self.parameters["Coil specs"]["Second Layer"]
        )
        self.clockwise_bool = self.parameters["Coil specs"]["Direction"]

    def BuildThisFootprint(self):
        self.odd_loops = (self.turns % 2) == 1
        self.odd_loops_multiplier = -1 if self.odd_loops else 1
        self.cw_multiplier = 1 if self.clockwise_bool else -1

        """Draw the outline circle as reference."""
        self.draw.SetLayer(pcbnew.User_1)
        self.draw.Circle(self.center_x, self.center_y, self.aperture_r)

        self.draw.SetLayer(pcbnew.F_Fab)
        self.draw.Value(0, 0, pcbnew.FromMM(1))
        self.draw.SetLayer(pcbnew.F_SilkS)
        self.draw.Reference(0, 0, pcbnew.FromMM(1))

        """ Calculate several of the internal variables needed. """
        via_d = self.via_ann_ring * 2 + self.via_hole
        pad_d = self.pad_ann_ring * 2 + self.pad_hole

        self.draw.SetLineThickness(self.trace_width)

        # Set the arc origins
        del_o_1 = max(via_d, self.trace_width) / 2 - self.trace_width / 2
        del_o_2 = max(via_d, self.trace_width) / 2 + self.trace_space / 2

        """
        Draw the starting via between the front and back layers
        """
        pad_number = 3
        pad = pcbnew.PAD(self.module)
        pad.SetSize(pcbnew.VECTOR2I(via_d, via_d))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        pad.SetDrillSize(pcbnew.VECTOR2I(self.via_hole, self.via_hole))

        pos = pcbnew.VECTOR2I(
            int(self.aperture_r + self.aperture_gap + max(via_d, self.trace_width) / 2)
            * self.odd_loops_multiplier,
            0,
        )
        pad.SetPosition(pos)
        pad.SetNumber(pad_number)
        pad.SetName(str(pad_number))
        self.module.Add(pad)

        """
        Draw the coils themselves
        """
        # Draw the first winding
        arc_center_x = self.center_x + del_o_1 / 2 * self.odd_loops_multiplier
        arc_start_x = (
            self.aperture_r + self.aperture_gap + max(via_d, self.trace_width) / 2
        ) * self.odd_loops_multiplier
        self.draw.SetLayer(self.first_layer)
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        self.draw.SetLayer(self.second_layer)
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )

        for ii in range(1, self.turns, 2):
            self.draw.SetLayer(self.first_layer)
            arc_center_x = self.center_x + del_o_2 * self.odd_loops_multiplier
            arc_start_x = (
                -(
                    self.aperture_r
                    + self.aperture_gap
                    + (ii / 2) * (self.trace_width + self.trace_space)
                    - 0.5 * self.trace_space
                )
                * self.odd_loops_multiplier
            )
            self.draw.Arc(
                arc_center_x,
                self.center_y,
                arc_start_x,
                self.center_y,
                pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
            )
            self.draw.SetLayer(self.second_layer)
            self.draw.Arc(
                arc_center_x,
                self.center_y,
                arc_start_x,
                self.center_y,
                pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
            )

        arc_start_x_max = arc_start_x

        for ii in range(2, self.turns, 2):
            self.draw.SetLayer(self.first_layer)
            arc_center_x = (
                self.center_x
                + del_o_1 * (0.5 if ii == 0 else 1) * self.odd_loops_multiplier
            )
            arc_start_x = (
                self.aperture_r
                + self.aperture_gap
                + max(via_d, self.trace_width)
                + (ii / 2) * (self.trace_width + self.trace_space)
                - 0.5 * self.trace_width
            ) * self.odd_loops_multiplier
            self.draw.Arc(
                arc_center_x,
                self.center_y,
                arc_start_x,
                self.center_y,
                pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
            )
            self.draw.SetLayer(self.second_layer)
            self.draw.Arc(
                arc_center_x,
                self.center_y,
                arc_start_x,
                self.center_y,
                pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
            )

        """
        Finish the inductor with nice tails and pads.
        """
        self.draw.SetLayer(self.first_layer)
        arc_start_x = (
            self.center_x
            + self.aperture_r
            + self.aperture_gap
            + (self.trace_width if self.odd_loops else max(via_d, self.trace_width))
            + (self.turns // 2) * (self.trace_space + self.trace_width)
            - self.trace_width / 2
        )
        arc_center_x = arc_start_x + max(via_d, self.trace_width) * 2
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(90 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        self.draw.SetLayer(self.second_layer)
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-90 * self.cw_multiplier, pcbnew.DEGREES_T),
        )

        pad = pcbnew.PAD(self.module)
        pad.SetSize(pcbnew.VECTOR2I(pad_d, pad_d))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        pad.SetDrillSize(pcbnew.VECTOR2I(self.pad_hole, self.pad_hole))

        pos = pcbnew.VECTOR2I(
            int(arc_center_x),
            -int(max(via_d, self.trace_width) * 2 * self.cw_multiplier),
        )
        pad.SetPosition(pos)
        pad.SetNumber(1)
        pad.SetName("1")
        self.module.Add(pad)
        pad = pad.Duplicate()

        pos = pcbnew.VECTOR2I(
            int(arc_center_x),
            int(max(via_d, self.trace_width)) * 2 * self.cw_multiplier,
        )
        pad.SetPosition(pos)
        pad.SetNumber(2)
        pad.SetName("2")
        self.module.Add(pad)

        """
        Add Net Tie Group to the footprint. This allows the DRC to understand 
        that the shorting traces are OK for this component
        """
        self.module.AddNetTiePadGroup("1,2,3")

        """
        Capture the parameters in the Fab layer
        """
        text_size = self.GetTextSize()  # IPC nominal
        fab_text_s = (
            f'Direction {"CW" if self.clockwise_bool else "CCW"}\n'
            f"Inner Diameter: {self.aperture_r/1e6}\n"
            f"Inner Ring Gap: {self.aperture_gap/1e6}\n"
            f"Turns: {self.turns}\n"
            f'Layers (Start->Finish): {self.parameters["Coil specs"]["First Layer"]}->{self.parameters["Coil specs"]["Second Layer"]}\n'
            f"Trace Width/space: {self.trace_width/1e6}/{self.trace_space/1e6}\n"
            f"Pad Drill/annular ring: {self.pad_hole/1e6}/{self.pad_ann_ring/1e6}\n"
            f"Via Drill/annular ring: {self.via_hole/1e6}/{self.via_ann_ring/1e6}"
        )
        fab_text = pcbnew.PCB_TEXT(self.module)
        fab_text.SetText(fab_text_s)
        fab_text.SetPosition(pcbnew.VECTOR2I(0, 0))
        fab_text.SetTextSize(pcbnew.VECTOR2I(text_size, text_size))
        fab_text.SetLayer(pcbnew.F_Fab)
        self.module.Add(fab_text)


class CoilGenerator1L1T(FootprintWizardBase.FootprintWizard):
    center_x = 0
    center_y = 0

    GetName = lambda self: "Coil Generator, single layer, 1 turn"
    GetDescription = lambda self: "Generates a single turn loop at a circular aperture."
    GetValue = lambda self: "Single coil, single layer"

    def GenerateParameterList(self):
        # Info about the coil itself.
        self.AddParam("Coil specs", "Stub Length", self.uMM, 5, min_value=0)
        self.AddParam(
            "Coil specs",
            "Layer",
            self.uString,
            "F_Cu",
            hint="Layer name.  Uses '_' instead of '.'",
        )
        self.AddParam(
            "Coil specs", "Direction", self.uBool, True, hint="Unused for now"
        )

        # Information about where this footprint needs to fit into.
        self.AddParam("Install Info", "Radius", self.uMM, 30)

        # Info about the fabrication capabilities
        self.AddParam("Fab Specs", "Trace Width", self.uMM, 0.2, min_value=0)
        self.AddParam("Fab Specs", "Trace Spacing", self.uMM, 0.2, min_value=0)
        self.AddParam("Fab Specs", "Pad Drill", self.uMM, 0.5, min_value=0)
        self.AddParam("Fab Specs", "Pad Annular Ring", self.uMM, 0.2, min_value=0)

    def CheckParameters(self):
        self.radius = self.parameters["Install Info"]["Radius"]

        self.trace_width = self.parameters["Fab Specs"]["Trace Width"]
        self.trace_space = self.parameters["Fab Specs"]["Trace Spacing"]
        self.pad_hole = self.parameters["Fab Specs"]["Pad Drill"]
        self.pad_ann_ring = self.parameters["Fab Specs"]["Pad Annular Ring"]

        self.layer = getattr(pcbnew, self.parameters["Coil specs"]["Layer"])
        self.clockwise_bool = self.parameters["Coil specs"]["Direction"]
        self.stub_length = self.parameters["Coil specs"]["Stub Length"]

    def BuildThisFootprint(self):
        self.cw_multiplier = 1 if self.clockwise_bool else -1

        """ Calculate several of the internal variables needed. """
        pad_d = self.pad_ann_ring * 2 + self.pad_hole
        radius1 = self.radius + self.trace_width / 2
        radius2 = self.trace_width

        theta2 = math.acos(
            (self.trace_space + max(pad_d, self.trace_width) / 2 + radius2)
            / (radius1 + radius2)
        )
        theta1 = math.pi / 2 - theta2

        self.draw.SetLayer(self.layer)
        self.draw.SetLineThickness(self.trace_width)

        """ Draw the main arc """
        arc_start_x = self.center_x + radius1 * math.cos(theta1)
        arc_start_y = self.center_y - radius1 * math.sin(theta1)
        self.draw.Arc(
            self.center_x,
            self.center_y,
            arc_start_x,
            arc_start_y,
            pcbnew.EDA_ANGLE(
                -2 * (math.pi - theta1) * self.cw_multiplier, pcbnew.RADIANS_T
            ),
        )

        """ Draw the stubs """
        arc_center_x = self.center_x + (radius1 + radius2) * math.cos(theta1)
        arc_center_y = self.center_y - (radius1 + radius2) * math.sin(theta1)
        self.draw.Arc(
            arc_center_x,
            arc_center_y,
            arc_start_x,
            arc_start_y,
            pcbnew.EDA_ANGLE(-theta2 * self.cw_multiplier, pcbnew.RADIANS_T),
        )
        self.draw.Arc(
            arc_center_x,
            -arc_center_y,
            arc_start_x,
            -arc_start_y,
            pcbnew.EDA_ANGLE(theta2 * self.cw_multiplier, pcbnew.RADIANS_T),
        )

        self.draw.Line(
            arc_center_x,
            max(pad_d, self.trace_width) / 2 + self.trace_space,
            arc_center_x + self.stub_length,
            max(pad_d, self.trace_width) / 2 + self.trace_space,
        )
        self.draw.Line(
            arc_center_x,
            -max(pad_d, self.trace_width) / 2 - self.trace_space,
            arc_center_x + self.stub_length,
            -max(pad_d, self.trace_width) / 2 - self.trace_space,
        )

        pad = pcbnew.PAD(self.module)
        pad.SetSize(pcbnew.VECTOR2I(pad_d, pad_d))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        pad.SetDrillSize(pcbnew.VECTOR2I(self.pad_hole, self.pad_hole))

        pos = pcbnew.VECTOR2I(
            int(arc_center_x + self.stub_length),
            -int(max(pad_d, self.trace_width) / 2 + self.trace_space)
            * self.cw_multiplier,
        )
        pad.SetPosition(pos)
        pad.SetNumber(1)
        pad.SetName("1")
        self.module.Add(pad)
        pad = pad.Duplicate()

        pos = pcbnew.VECTOR2I(
            int(arc_center_x + self.stub_length),
            int(max(pad_d, self.trace_width) / 2 + self.trace_space)
            * self.cw_multiplier,
        )
        pad.SetPosition(pos)
        pad.SetNumber(2)
        pad.SetName("2")
        self.module.Add(pad)

        """
        Add Net Tie Group to the footprint. This allows the DRC to understand 
        that the shorting traces are OK for this component
        """
        self.module.AddNetTiePadGroup("1,2")

        """
        Capture the parameters in the Fab layer
        """
        text_size = self.GetTextSize()  # IPC nominal
        fab_text_s = (
            f'Direction {"CCW" if self.clockwise_bool else "CW"}\n'
            f"Diameter: {self.radius/1e6}\n"
            f'Layer: {self.parameters["Coil specs"]["Layer"]}\n'
            f"Trace Width/space: {self.trace_width/1e6}/{self.trace_space/1e6}\n"
            f"Pad Drill/annular ring: {self.pad_hole/1e6}/{self.pad_ann_ring/1e6}\n"
            f"Stub Length: {self.stub_length/1e6}"
        )
        fab_text = pcbnew.PCB_TEXT(self.module)
        fab_text.SetText(fab_text_s)
        fab_text.SetPosition(pcbnew.VECTOR2I(0, 0))
        fab_text.SetTextSize(pcbnew.VECTOR2I(text_size, text_size))
        fab_text.SetLayer(pcbnew.F_Fab)
        self.module.Add(fab_text)
