import pcbnew
import FootprintWizardBase
import math
'''
TODOS
1. Handle the single turn condition.  

'''

class CoilGeneratorID2L(FootprintWizardBase.FootprintWizard):
    center_x = 0
    center_y = 0

    GetName = lambda self: "Coil Generator from ID"
    GetDescription = (
        lambda self: "Generates a flux-neutral coil within a circular aperture."
    )
    GetValue = lambda self: "Coil based on ID"

    def GenerateParameterList(self):
        # Info about the coil itself.
        self.AddParam("Coil specs", "Total Turns", self.uInteger, 5, min_value=1)
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
            "B_Cu", # "In1_Cu",
            hint="Layer name.  Uses '_' instead of '.'",
        )
        self.AddParam("Coil specs", "Direction", self.uBool, True, hint="Unused for now")

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
        self.AddParam("Fab Specs", "Trace Width", self.uMM, 1, min_value=0)
        self.AddParam("Fab Specs", "Trace Spacing", self.uMM, 1, min_value=0)
        self.AddParam("Fab Specs", "Via Drill", self.uMM, 0.3, min_value=0, hint="Diameter")
        self.AddParam("Fab Specs", "Via Annular Ring", self.uMM, 0.15, min_value=0, hint="Radius")
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
        self.min_radius = self.parameters["Coil specs"]["Minimum Radius"]
        self.stub_length = self.parameters["Coil specs"]["Stub Length"]
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
        # pitch = (
        #         self.trace_space
        #         + self.trace_width / 2
        #         + max(self.trace_width / 2, self.via_hole / 2 + self.via_ann_ring)
        # )

        # # Pythagorean Theorem to determine via spacing
        # aa = (
        #     self.via_hole / 2
        #     + self.via_ann_ring
        #     + self.trace_space
        #     + self.trace_width / 2
        # )
        # cc = self.via_ann_ring * 2 + self.via_hole + self.trace_space
        # via_gap = math.sqrt(cc * cc - aa * aa)  # units of KiCAD_internal
        via_d = self.via_ann_ring * 2 + self.via_hole

        self.draw.SetLineThickness(self.trace_width)

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

        pos = pcbnew.VECTOR2I(int(self.aperture_r + self.aperture_gap + max(via_d, self.trace_width)/2) *
                              self.odd_loops_multiplier, 0)
        pad.SetPosition(pos)
        pad.SetPos0(pos)
        pad.SetNumber(pad_number)
        pad.SetName(str(pad_number))
        self.module.Add(pad)

        # Draw the first Arc
        del_o_1 = (max(via_d, self.trace_width)/2 - self.trace_width/2)/2
        arc_center_x = self.center_x + del_o_1 * self.odd_loops_multiplier
        arc_start_x = (self.aperture_r + self.aperture_gap + max(via_d, self.trace_width)/2) * \
                      self.odd_loops_multiplier
        self.draw.SetLayer(self.first_layer)
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     self.center_y,
        #     arc_start_x,
        #     self.center_y,
        #     pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        # )

        # Draw the second loop
        del_o_2 = max(via_d, self.trace_width)/2 + self.trace_space/2
        self.draw.SetLayer(self.first_layer)
        arc_center_x = self.center_x + del_o_2 * self.odd_loops_multiplier
        arc_start_x = -(self.aperture_r + self.aperture_gap + 0.5 * self.trace_width) * self.odd_loops_multiplier
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     self.center_y,
        #     arc_start_x,
        #     self.center_y,
        #     pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        # )

        # Draw third loop
        self.draw.SetLayer(self.first_layer)
        arc_center_x = self.center_x + (del_o_2 - self.trace_space/2 - self.trace_width/2) * self.odd_loops_multiplier
        arc_start_x = (self.aperture_r + self.aperture_gap + max(via_d, self.trace_width) + 0.5 * self.trace_width +  self.trace_space)\
                      * self.odd_loops_multiplier
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     self.center_y,
        #     arc_start_x,
        #     self.center_y,
        #     pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        # )

        # Draw fourth Loop
        self.draw.SetLayer(self.first_layer)
        arc_center_x = self.center_x + del_o_2 * self.odd_loops_multiplier
        arc_start_x = -(self.aperture_r + self.aperture_gap + 1.5 * self.trace_width + self.trace_space) * self.odd_loops_multiplier
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     self.center_y,
        #     arc_start_x,
        #     self.center_y,
        #     pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        # )

        # Draw Fifth Loop
        self.draw.SetLayer(self.first_layer)
        arc_center_x = self.center_x + (del_o_2 - self.trace_space/2 - self.trace_width/2) * self.odd_loops_multiplier
        arc_start_x = ( self.aperture_r + self.aperture_gap + max(via_d, self.trace_width) + 1.5 * self.trace_width + 2 * self.trace_space) * \
                      self.odd_loops_multiplier
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     self.center_y,
        #     arc_start_x,
        #     self.center_y,
        #     pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        # )

        # Draw Sixth Loop
        self.draw.SetLayer(self.first_layer)
        arc_center_x = self.center_x + del_o_2 * self.odd_loops_multiplier
        arc_start_x = -(
                    self.aperture_r + self.aperture_gap + 2.5 * self.trace_width + 2* self.trace_space) * self.odd_loops_multiplier
        self.draw.Arc(
            arc_center_x,
            self.center_y,
            arc_start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-180 * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     self.center_y,
        #     arc_start_x,
        #     self.center_y,
        #     pcbnew.EDA_ANGLE(180 * self.cw_multiplier, pcbnew.DEGREES_T),
        # )




        # """ Draw the large curves defining the bulk of the coil"""
        # arc_center_x = (
        #     self.center_x - pitch * (self.turns - 1) / 2 - self.min_radius - via_gap
        # )
        # arc_center_y = self.center_y
        # arc_start_x = arc_center_x
        # arc_start_y = (
        #     arc_center_y
        #     + self.aperture_r
        #     - self.aperture_gap
        #     - pitch * (self.turns - 1) / 2
        #     - self.min_radius
        #     - via_gap
        # )

        # for ii in range(self.turns):
        #     self.draw.SetLayer(self.first_layer)
        #     self.draw.Arc(
        #         arc_center_x,
        #         arc_center_y,
        #         arc_start_x,
        #         arc_start_y - ii * pitch,
        #         pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T),
        #     )
        #     self.draw.SetLayer(self.second_layer)
        #     self.draw.Arc(
        #         -arc_center_x,
        #         -arc_center_y,
        #         -arc_start_x,
        #         -arc_start_y + ii * pitch,
        #         pcbnew.EDA_ANGLE(180, pcbnew.DEGREES_T),
        #     )


        # """
        # Draw Horizontal Lines.  These are needed to give space to the vias for
        # stacking.  Otherwise, the coils would need to be further apart.
        # """
        # # Draw the simple ones first
        # self.draw.SetLayer(self.second_layer)
        # for ii in range(self.turns):
        #     self.draw.Line(
        #         -arc_start_x,
        #         -arc_start_y + ii * pitch,
        #         -arc_start_x - via_gap,
        #         -arc_start_y + ii * pitch,
        #     )
        # self.draw.SetLayer(self.first_layer)
        # for ii in range(1, self.turns):
        #     self.draw.Line(
        #         arc_start_x,
        #         -arc_start_y + ii * pitch,
        #         arc_start_x + via_gap + pitch,
        #         -arc_start_y + ii * pitch,
        #     )

        # # Draw alternating Horizontal Lines for Vias
        # for ii in range(self.turns):
        #     if (ii % 2) == 1:
        #         self.draw.SetLayer(self.first_layer)
        #     else:
        #         self.draw.SetLayer(self.second_layer)
        #     self.draw.Line(
        #         arc_start_x,
        #         arc_start_y - ii * pitch,
        #         arc_start_x + via_gap,
        #         arc_start_y - ii * pitch,
        #     )

        #     if (ii % 2) == 1:
        #         self.draw.SetLayer(self.second_layer)
        #     else:
        #         self.draw.SetLayer(self.first_layer)

        #     self.draw.Line(
        #         -arc_start_x,
        #         arc_start_y - ii * pitch,
        #         -arc_start_x - via_gap,
        #         arc_start_y - ii * pitch,
        #     )

        # """
        # Draw the stitching vias between the front and back layers
        # """
        # pad_number = 3
        # pad = pcbnew.PAD(self.module)
        # pad.SetSize(pcbnew.VECTOR2I(via_d, via_d))
        # pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        # pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        # pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        # pad.SetDrillSize(pcbnew.VECTOR2I(self.via_hole, self.via_hole))

        # for ii in range(self.turns):
        #     if (ii % 2) == 1:
        #         offset = via_gap
        #     else:
        #         offset = 0
        #     pos = pcbnew.VECTOR2I(
        #         int(arc_start_x + offset), int(arc_start_y - ii * pitch)
        #     )
        #     pad.SetPosition(pos)
        #     pad.SetPos0(pos)
        #     pad.SetNumber(pad_number)
        #     pad.SetName(str(pad_number))
        #     self.module.Add(pad)
        #     pad = (
        #         pad.Duplicate()
        #     )  # needed because otherwise you keep editing the same object.

        #     pos = pcbnew.VECTOR2I(
        #         int(-arc_start_x - offset), int(arc_start_y - ii * pitch)
        #     )
        #     pad.SetPosition(pos)
        #     pad.SetPos0(pos)
        #     pad.SetNumber(pad_number)
        #     pad.SetName(str(pad_number))
        #     self.module.Add(pad)
        #     pad = pad.Duplicate()

        # """
        # Draw the tap points from the coil.  

        # The Front layer is easy.  The Back layer requres a little bit of work
        # and a via to get out.  
        # """
        # # Draw arc and trace from outer coil
        # self.draw.SetLayer(self.first_layer)
        # self.draw.Arc(
        #     arc_center_x,
        #     -arc_start_y - aa,
        #     arc_center_x,
        #     -arc_start_y,
        #     pcbnew.EDA_ANGLE(-90, pcbnew.DEGREES_T),
        # )
        # self.draw.Line(
        #     arc_center_x + aa,
        #     -arc_start_y - aa,
        #     arc_center_x + aa,
        #     -arc_start_y - aa - self.stub_length,
        # )

        # # Add Pad for one side of the coil
        # pos = pcbnew.VECTOR2I(
        #     int(arc_center_x + aa), int(-arc_start_y - aa - self.stub_length)
        # )
        # pad = pcbnew.PAD(self.module)
        # pad.SetSize(
        #     pcbnew.VECTOR2I(
        #         self.pad_ann_ring + self.pad_hole, self.pad_ann_ring + self.pad_hole
        #     )
        # )
        # pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        # pad.SetLayerSet(pad.PTHMask())
        # pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        # pad.SetDrillSize(pcbnew.VECTOR2I(self.pad_hole, self.pad_hole))
        # pad.SetPos0(pos)
        # pad.SetPosition(pos)
        # pad.SetNumber(1)
        # pad.SetName("1")
        # pad.SetLayer(self.first_layer)
        # self.module.Add(pad)

        # # Diagonal track to get to via
        # self.draw.Line(
        #     -start_x, -line_length + aa * 2, -start_x - aa, -line_length + aa
        # )
        # # Add Via
        # pos = pcbnew.VECTOR2I(int(-start_x - aa), int(-line_length + aa))
        # pad = pcbnew.PAD(self.module)
        # pad.SetSize(pcbnew.VECTOR2I(via_d, via_d))
        # pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        # pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        # pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        # pad.SetDrillSize(pcbnew.VECTOR2I(self.via_hole, self.via_hole))
        # pad.SetNumber(pad_number)
        # pad.SetName(str(pad_number))
        # pad_number += 1
        # pad.SetPos0(pos)
        # pad.SetPosition(pos)
        # self.module.Add(pad)

        # # Vertical track to get under the coils.
        # self.draw.SetLayer(self.second_layer)
        # self.draw.Line(
        #     -start_x - aa,
        #     -line_length + aa,
        #     -start_x - aa,
        #     -line_length - aa - (self.turns - 1) * pitch - self.stub_length,
        # )

        # # Jogging right to clear space for Vias
        # self.draw.Line(
        #     -start_x - aa,
        #     -line_length - aa - (self.turns - 1) * pitch - self.stub_length,
        #     -start_x - aa + self.min_radius,
        #     -line_length
        #     - aa
        #     - (self.turns - 1) * pitch
        #     - self.stub_length
        #     - self.min_radius,
        # )

        # # Add pad for other side of the coil
        # pos = pcbnew.VECTOR2I(
        #     int(-start_x - aa + self.min_radius),
        #     int(-arc_start_y - aa - self.stub_length),
        # )
        # pad = pcbnew.PAD(self.module)
        # pad.SetSize(
        #     pcbnew.VECTOR2I(
        #         self.pad_ann_ring + self.pad_hole, self.pad_ann_ring + self.pad_hole
        #     )
        # )
        # pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        # pad.SetLayerSet(pad.PTHMask())
        # pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        # pad.SetDrillSize(pcbnew.VECTOR2I(self.pad_hole, self.pad_hole))
        # pad.SetPos0(pos)
        # pad.SetPosition(pos)
        # pad.SetNumber(2)
        # pad.SetName("2")
        # self.module.Add(pad)

        # """
        # Add Net Tie Group to the footprint. This allows the DRC to understand 
        # that the shorting traces are OK for this component
        # """
        # self.module.AddNetTiePadGroup("1,2,3")
