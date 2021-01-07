# -*- coding: UTF-8 -*-

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
'                                                                         '
' Copyright 2018 Gauthier Brière (gauthier.briere "at" gmail.com)         '
'                                                                         '
' This file is part of cn5X++                                               '
'                                                                         '
' cn5X++ is free software: you can redistribute it and/or modify it         '
'  under the terms of the GNU General Public License as published by      '
' the Free Software Foundation, either version 3 of the License, or       '
' (at your option) any later version.                                     '
'                                                                         '
' cn5X++ is distributed in the hope that it will be useful, but           '
' WITHOUT ANY WARRANTY; without even the implied warranty of              '
' MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           '
' GNU General Public License for more details.                            '
'                                                                         '
' You should have received a copy of the GNU General Public License       '
' along with this program.  If not, see <http://www.gnu.org/licenses/>.   '
'                                                                         '
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

def grblSetting(num):

  return (grblSettingsCodes[num][0]
       + " (" + grblSettingsCodes[num][1] + ")"
       + " : " + grblSettingsCodes[num][2]
  )

# "$-Code"," Setting"," Units"," Setting Description"
grblSettingsCodes = {
  0: ["Step pulse time", "microseconds", "Sets time length per step. Minimum 3usec."],
  1: ["Step idle delay", "milliseconds", "Sets a short hold delay when stopping to let dynamics settle before disabling steppers. Value 255 keeps motors enabled with no delay."],
  2: ["Step pulse invert", "mask", "Inverts the step signal. Set axis bit to invert (00000ZYX)."],
  3: ["Step direction invert", "mask", "Inverts the direction signal. Set axis bit to invert (00000ZYX)."],
  4: ["Invert step enable pin", "boolean", "Inverts the stepper driver enable pin signal."],
  5: ["Invert limit pins", "boolean", "Inverts the all of the limit input pins."],
  6: ["Invert probe pin", "boolean", "Inverts the probe input pin signal."],
  10: ["Status report options", "mask", "Alters data included in status reports."],
  11: ["Junction deviation", "millimeters", "Sets how fast Grbl travels through consecutive motions. Lower value slows it down."],
  12: ["Arc tolerance", "millimeters", "Sets the G2 and G3 arc tracing accuracy based on radial error. Beware: A very small value may effect performance."],
  13: ["Report in inches", "boolean", "Enables inch units when returning any position and rate value that is not a settings value."],
  20: ["Soft limits enable", "boolean", "Enables soft limits checks within machine travel and sets alarm when exceeded. Requires homing."],
  21: ["Hard limits enable", "boolean", "Enables hard limits. Immediately halts motion and throws an alarm when switch is triggered."],
  22: ["Homing cycle enable", "boolean", "Enables homing cycle. Requires limit switches on all axes."],
  23: ["Homing direction invert", "mask", "Homing searches for a switch in the positive direction. Set axis bit (00000ZYX) to search in negative direction."],
  24: ["Homing locate feed rate", "units (millimeters or degres)/min", "Feed rate to slowly engage limit switch to determine its location accurately."],
  25: ["Homing search seek rate", "units (millimeters or degres)/min", "Seek rate to quickly find the limit switch before the slower locating phase."],
  26: ["Homing switch debounce delay", "milliseconds", "Sets a short delay between phases of homing cycle to let a switch debounce."],
  27: ["Homing switch pull-off distance", "millimeters", "Retract distance after triggering switch to disengage it. Homing will fail if switch isn't cleared."],
  30: ["Maximum spindle speed", "RPM", "Maximum spindle speed. Sets PWM to 100% duty cycle."],
  31: ["Minimum spindle speed", "RPM", "Minimum spindle speed. Sets PWM to 0.4% or lowest duty cycle."],
  32: ["Laser-mode enable", "boolean", "Enables laser mode. Consecutive G1/2/3 commands will not halt when spindle speed is changed."],
  100: ["1st axis travel resolution", "step/unit", "1st axis travel resolution in steps per unit (millimeter or degre)."],
  101: ["2nd axis travel resolution", "step/unit", "2nd axis travel resolution in steps per unit (millimeter or degre)."],
  102: ["3rd axis travel resolution", "step/unit", "3rd axis travel resolution in steps per unit (millimeter or degre)."],
  103: ["4th axis travel resolution", "step/unit", "4th axis travel resolution in steps per unit (millimeter or degre)"],
  104: ["5th axis travel resolution", "step/unit", "5th axis travel resolution in steps per unit (millimeter or degre)"],
  105: ["6th axis travel resolution", "step/unit", "6th axis travel resolution in steps per unit (millimeter or degre)"],
  110: ["1st axis maximum rate", "unit/min", "1st axis maximum rate. Used as G0 rapid rate."],
  111: ["2nd axis maximum rate", "unit/min", "2nd axis maximum rate. Used as G0 rapid rate."],
  112: ["3rd axis maximum rate", "unit/min", "3rd axis maximum rate. Used as G0 rapid rate."],
  113: ["4th axis maximum rate", "unit/min", "4th axis maximum rate. Used as G0 rapid rate"],
  114: ["5th axis maximum rate", "unit/min", "5th axis maximum rate. Used as G0 rapid rate"],
  115: ["6th axis maximum rate", "unit/min", "6th axis maximum rate. Used as G0 rapid rate"],
  120: ["1st axis acceleration", "unit/sec^2", "1st axis acceleration. Used for motion planning to not exceed motor torque and lose steps."],
  121: ["2nd axis acceleration", "unit/sec^2", "2nd axis acceleration. Used for motion planning to not exceed motor torque and lose steps."],
  122: ["3rd axis acceleration", "unit/sec^2", "3rd axis acceleration. Used for motion planning to not exceed motor torque and lose steps."],
  123: ["4th axis acceleration", "unit/sec^2", "4th axis acceleration. Used for motion planning to not exceed motor torque and lose steps."],
  124: ["5th axis acceleration", "unit/sec^2", "5th axis acceleration. Used for motion planning to not exceed motor torque and lose steps."],
  125: ["6th axis acceleration", "unit/sec^2", "5th axis acceleration. Used for motion planning to not exceed motor torque and lose steps."],
  130: ["1st axis maximum travel", "unit (millimeters or degres)", "Maximum 1st axis travel distance from homing switch. Determines valid machine space for soft-limits and homing search distances."],
  131: ["2nd axis maximum travel", "unit (millimeters or degres)", "Maximum 2nd axis travel distance from homing switch. Determines valid machine space for soft-limits and homing search distances."],
  132: ["3rd axis maximum travel", "unit (millimeters or degres)", "Maximum 3rd axis travel distance from homing switch. Determines valid machine space for soft-limits and homing search distances."],
  133: ["4th axis maximum travel", "unit (millimeters or degres)", "Maximum 4th axis travel distance from homing switch. Determines valid machine space for soft-limits and homing search distances."],
  134: ["5th axis maximum travel", "unit (millimeters or degres)", "Maximum 5th axis travel distance from homing switch. Determines valid machine space for soft-limits and homing search distances."],
  135: ["6th axis maximum travel", "unit (millimeters or degres)", "Maximum 6th axis travel distance from homing switch. Determines valid machine space for soft-limits and homing search distances."]
}
