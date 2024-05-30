import pcbnew
import FootprintWizardBase
import math

TRACE_THICKNESS_1OZ = 0.035e-3  # 35um in meters
RHO = 1.678e-8  # Copper resistivity (ohm-mm)


class PCBTraceComponent(FootprintWizardBase.FootprintWizard):
    trace_length = 0.0
    vias = 0
    center_y = 0.0
    cw_multiplier = 1
    netTiePadGroupSet = set([])

    def DrawArcsYSym2Layer(self, layer1, layer2, center_x, start_x, degrees):
        self.draw.SetLayer(layer1)
        self.draw.Arc(
            center_x,
            self.center_y,
            start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(-degrees * self.cw_multiplier, pcbnew.DEGREES_T),
        )
        self.draw.SetLayer(layer2)
        self.draw.Arc(
            center_x,
            self.center_y,
            start_x,
            self.center_y,
            pcbnew.EDA_ANGLE(degrees * self.cw_multiplier, pcbnew.DEGREES_T),
        )

        """
        Calculate the length of the arc and add it to the total trace length
        """
        arc_length = abs(center_x - start_x) * math.pi * abs(degrees) / 180
        self.trace_length += arc_length * 2  # Two arcs
        temp = self.trace_width

    def GetResistance(self):
        return (
            RHO
            * (self.trace_length / 1e9)
            / (TRACE_THICKNESS_1OZ * self.copper_thickness * self.trace_width / 1e9)
        )

    def DrawText(self, text, layer):
        text_size = self.GetTextSize()  # IPC nominal
        fab_text = pcbnew.PCB_TEXT(self.module)
        fab_text.SetText(text)
        fab_text.SetPosition(pcbnew.VECTOR2I(0, 0))
        fab_text.SetTextSize(pcbnew.VECTOR2I(text_size, text_size))
        fab_text.SetLayer(layer)
        fab_text.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        self.module.Add(fab_text)

    def PlacePad(self, number: int, position, pad_diameter, pad_hole, via=False):
        pad = pcbnew.PAD(self.module)
        pad.SetSize(pcbnew.VECTOR2I(pad_diameter, pad_diameter))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        pad.SetDrillSize(pcbnew.VECTOR2I(pad_hole, pad_hole))
        pad.SetPosition(position)
        pad.SetNumber(number)
        pad.SetName(str(number))
        self.module.Add(pad)

        if via:
            self.vias += 1

        self.netTiePadGroupSet.add(number)

    def GenerateNetTiePadGroup(self):
        # TODO: It feels like there should be a more Pythonic way to make this string
        s = ""
        for ii in self.netTiePadGroupSet:
            s += str(ii) + ","
        self.module.AddNetTiePadGroup(s[:-1])
