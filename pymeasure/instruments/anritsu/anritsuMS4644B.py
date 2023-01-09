#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2023 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import logging

from pymeasure.instruments import Instrument, Channel
from pymeasure.instruments.validators import (
    strict_discrete_set,
    strict_range
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Port(Channel):
    placeholder = "pt"

    power_level = Channel.control(
        ":SOUR{{ch}}:POW:PORT{pt}?", ":SOUR{{ch}}:POW:PORT{pt} %g",
        """Control the power level (in dBm) of the indicated port on the indicated channel. """,
        values=[-3E1, 3E1],
        validator=strict_range,
    )


class Trace(Channel):
    placeholder = "tr"

    def activate(self):
        """ Sets the indicated trace as the active one. """
        self.write(":CALC{{ch}}:PAR{tr}:SEL")

    SPARAM_LIST = ["S11", "S12", "S21", "S22",
                   "S13", "S23", "S33", "S31",
                   "S32", "S14", "S24", "S34",
                   "S41", "S42", "S43", "S44", ]

    measurement_parameter = Channel.control(
        ":CALC{{ch}}:PAR{tr}:DEF?", ":CALC{{ch}}:PAR{tr}:DEF %s",
        """Control the measurement parameter of the indicated trace.

        Valid values are any S-parameter (e.g. S11, S12, S41) for 4 ports, or one of the
        following:

        =====   ================================================================
        value   description
        =====   ================================================================
        Sxx     S-parameters (1-4 for both x)
        MIX     Response Mixed Mode
        NFIG    Noise Figure trace response (only with option 41 or 48)
        NPOW    Noise Power trace response (only with option 41 or 48)
        NTEMP   Noise Temperature trace response (only with option 41 or 48)
        AGA     Noise Figure Available Gain trace response (only with option 48)
        IGA     Noise Figure Insertion Gain trace response (only with option 48)
        =====   ================================================================
        """,
        values=SPARAM_LIST + ["MIX", "NFIG", "NPOW", "NTEMP", "AGA", "IGA"],
        validator=strict_discrete_set,
    )


class MeasurementChannel(Channel):
    FREQUENCY_RANGE = [1E7, 4E10]
    TRACES = [1, 16]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for pt in range(self.parent.PORTS[1]):
            self.add_child(Port, pt + 1, collection="ports", prefix="pt_")
        for tr in range(self.TRACES[1]):
            self.add_child(Trace, tr + 1, collection="traces", prefix="tr_")

    def check_errors(self):
        return self.parent.check_errors()

    def activate(self):
        """ Sets the indicated channel as the active channel. """
        self.write(":DISP:WIND{ch}:ACT")

    number_of_traces = Channel.control(
        ":CALC{ch}:PAR:COUN?", ":CALC{ch}:PAR:COUN %d",
        """Control the number of traces on the specified channel

        Valid values are between 1 and 16.
        """,
        values=TRACES,
        validator=strict_range,
        cast=int,
    )

    active_trace = Instrument.setting(
        ":CALC{ch}:PAR%d:SEL",
        """Set the active trace on the indicated channel. """,
        values=TRACES,
        validator=strict_range,
    )

    DISPLAY_LAYOUTS = ["R1C1", "R1C2", "R2C1", "R1C3", "R3C1",
                       "R2C2C1", "R2C1C2", "C2R2R1", "C2R1R2",
                       "R1C4", "R4C1", "R2C2", "R2C3", "R3C2",
                       "R2C4", "R4C2", "R3C3", "R5C2", "R2C5",
                       "R4C3", "R3C4", "R4C4"]
    display_layout = Channel.control(
        ":DISP:WIND{ch}:SPL?", ":DISP:WIND{ch}:SPL %s",
        """Control the trace display layout in a Row-by-Column format for the indicated channel.

        Valid values are: {}. The number following the R indicates the number of rows, following the
        C the number of columns.
        """.format(", ".join(DISPLAY_LAYOUTS)),
        values=DISPLAY_LAYOUTS,
        validator=strict_discrete_set,
        cast=int,
    )

    application_type = Channel.control(
        ":CALC{ch}:APPL:MEAS:TYP?", ":CALC{ch}:APPL:MEAS:TYP %s",
        """Control the application type of the specified channel.

        Valid values are TRAN (for transmission/reflection), NFIG (for noise figure measurement),
        PULS (for PulseView).
        """,
        values=["TRAN", "NFIG", "PULS"],
        validator=strict_discrete_set,
    )

    hold_function = Channel.control(
        ":SENS{ch}:HOLD:FUNC?", ":SENS{ch}:HOLD:FUNC %s",
        """Control the hold function of the specified channel.

        valid values are:

        =====   =================================================
        value   description
        =====   =================================================
        CONT    Perform continuous sweeps on all channels
        HOLD    Hold the sweep on all channels
        SING    Perform a single sweep and then hold all channels
        =====   =================================================
        """,
        values=["CONT", "HOLD", "SING"],
        validator=strict_discrete_set,
    )

    cw_mode_enabled = Channel.control(
        ":SENS{ch}:SWE:CW?", ":SENS{ch}:SWE:CW %d",
        """Control the state of the CW sweep mode of the indicated channel. """,
        values={True: 1, False: 0},
        map_values=True,
    )

    cw_number_of_points = Channel.control(
        ":SENS{ch}:SWE:CW:POIN?", ":SENS{ch}:SWE:CW:POIN %g",
        """Control the CW sweep mode number of points of the indicated channel.

        Valid values are between 1 and 25000 or 100000 depending on the maximum points setting.
        """,
        values=[1, 100000],
        validator=strict_range,
        cast=int,
    )

    number_of_points = Channel.control(
        "SENS{ch}:SWE:POIN?", "SENS{ch}:SWE:POIN %g",
        """Control the number of measurement points in a frequency sweep of the indicated channel.

        Valid values are between 1 and 25000 or 100000 depending on the maximum points setting.
        """,
        values=[1, 100000],
        validator=strict_range,
        cast=int,
    )

    frequency_start = Channel.control(
        ":SENS{ch}:FREQ:STAR?", ":SENS{ch}:FREQ:STAR %g",
        """Control the start value of the sweep range of the indicated channel in hertz.

        Valid values are between 1E7 [Hz] (i.e. 10 MHz) and 4E10 [Hz] (i.e. 40 GHz).
        """,
        values=FREQUENCY_RANGE,
        validator=strict_range,
    )

    frequency_stop = Channel.control(
        ":SENS{ch}:FREQ:STOP?", ":SENS{ch}:FREQ:STOP %g",
        """Control the stop value of the sweep range of the indicated channel in hertz.

        Valid values are between 1E7 [Hz] (i.e. 10 MHz) and 4E10 [Hz] (i.e. 40 GHz).
        """,
        values=FREQUENCY_RANGE,
        validator=strict_range,
    )

    frequency_span = Channel.control(
        ":SENS{ch}:FREQ:SPAN?", ":SENS{ch}:FREQ:SPAN %g",
        """Control the span value of the sweep range of the indicated channel in hertz.

        Valid values are between 1E7 [Hz] (i.e. 10 MHz) and 4E10 [Hz] (i.e. 40 GHz).
        """,
        values=FREQUENCY_RANGE,
        validator=strict_range,
    )

    frequency_center = Channel.control(
        ":SENS{ch}:FREQ:CENT?", ":SENS{ch}:FREQ:CENT %g",
        """Control the center value of the sweep range of the indicated channel in hertz.

        Valid values are between 1E7 [Hz] (i.e. 10 MHz) and 4E10 [Hz] (i.e. 40 GHz).
        """,
        values=FREQUENCY_RANGE,
        validator=strict_range,
    )

    frequency_CW = Channel.control(
        ":SENS{ch}:FREQ:CW?", ":SENS{ch}:FREQ:CW %g",
        """Control the CW frequency of the indicated channel in hertz.

        Valid values are between 1E7 [Hz] (i.e. 10 MHz) and 4E10 [Hz] (i.e. 40 GHz).
        """,
        values=FREQUENCY_RANGE,
        validator=strict_range,
    )

    def clear_average_count(self):
        """ Clears and restarts the averaging sweep count of the indicated channel. """
        self.write(":SENS{ch}:AVER:CLE")

    average_count = Channel.control(
        ":SENS{ch}:AVER:COUN?", ":SENS{ch}:AVER:COUN %d",
        """Control the averaging count for the indicated channel.

        The channel must be turned on. Valid values are between 1 and 1024.
        """,
        values=[1, 1024],
        validator=strict_range,
        cast=int,
    )

    average_sweep_count = Channel.measurement(
        ":SENS{ch}:AVER:SWE?",
        """Get the averaging sweep count for the indicated channel. """,
        cast=int,
    )

    average_type = Channel.control(
        ":SENS{ch}:AVER:TYP?", ":SENS{ch}:AVER:TYP %s",
        """Control the averaging type to for the indicated channel.

        Valid values are POIN (point-by-point) or SWE (sweep-by-sweep)
        """,
        values=["POIN", "SWE"],
        validator=strict_discrete_set,
    )

    averaging_enabled = Channel.control(
        ":SENS{ch}:AVER?", ":SENS{ch}:AVER %d",
        """Control whether the averaging is turned on for the indicated channel. """,
        values={True: 1, False: 0},
        map_values=True,
    )

    bandwidth = Channel.control(
        ":SENS{ch}:BWID?", ":SENS{ch}:BWID %g",
        """Control the IF bandwidth for the indicated channel.

        Valid values are between 1 [Hz] and 1E6 [Hz] (i.e. 1 MHz). The system will automatically
        select the closest IF bandwidth from the available options (1, 3, 10 ... 1E5, 3E5, 1E6).
        """,
        values=[1, 1E6],
        validator=strict_range,
    )

    calibration_enabled = Channel.control(
        ":SENS{ch}:CORR:STAT?", ":SENS{ch}:CORR:STAT %d",
        """Control whether the RF correction (calibration) is enabled for indicated channel. """,
        values={True: 1, False: 0},
        map_values=True,
    )


class AnritsuMS4644B(Instrument):
    """ A class representing the Anritsu MS4644B Vector Network Analyzer (VNA).

    """
    CHANNELS = [1, 16]
    TRACES = [1, 16]
    PORTS = [1, 4]  # TODO: check number: 4 or 7/8
    TRIGGER_TYPES = ["POIN", "SWE", "CHAN", "ALL"]

    def __init__(self, adapter, **kwargs):
        super().__init__(
            adapter,
            "Anritsu MS4644B Vector Network Analyzer",
            timeout=10000,
            **kwargs,
        )

        for ch in range(self.CHANNELS[1]):
            self.add_child(MeasurementChannel, ch+1)

    def check_errors(self):
        """ Read all errors from the instrument.

        :return: list of error entries
        """
        errors = []
        while True:
            err = self.values("SYST:ERR?")
            if err[0] != "No Error":
                log.error(f"{self.name}: {err[0]}")
                print(err)  # TODO: remove this line
                errors.append(err)
            else:
                break
        return errors

    datablock_header_format = Instrument.control(
        "FDHX?", "FDH%d",
        """Control the way the arbitrary block header for output data is formed.

        Valid values are:

        =====    ===========================================================
        value    description
        =====    ===========================================================
        0        A block header with arbitrary length will be sent.
        1        The block header will have a fixed length of 11 characters.
        2        No block header will be sent. Not IEEE 488.2 compliant.
        =====    ===========================================================
        """,
        values=[0, 1, 2],
        validator=strict_discrete_set,
        cast=int,
    )

    datafile_frequency_unit = Instrument.control(
        ":FORM:SNP:FREQ?", ":FORM:SNP:FREQ %s",
        """Control the frequency unit displayed in an SNP data file.

        Valid values are HZ, KHZ, MHZ, GHZ.
        """,
        values=["HZ", "KHZ", "MHZ", "GHZ"],
        validator=strict_discrete_set,
    )

    datablock_numeric_format = Instrument.control(
        ":FORM:DATA?", ":FORM:DATA %s",
        """Control format for numeric I/O data representation.

        Valid values are:

        =====   ==========================================================================
        value   description
        =====   ==========================================================================
        ASCII   An ASCII number of 20 or 21 characters long with floating point notation.
        8byte   8 bytes of binary floating point number representation limited to 64 bits.
        4byte   4 bytes of floating point number representation.
        =====   ==========================================================================
        """,
        values={"ASCII": "ASC", "8byte": "REAL", "4byte": "REAL32"},
        map_values=True,
    )

    datafile_include_heading = Instrument.control(
        ":FORM:DATA:HEAD?", ":FORM:DATA:HEAD %d",
        """Control whether a heading is included in the data files. """,
        values={True: 1, False: 0},
        map_values=True,
    )

    datafile_parameter_format = Instrument.control(
        ":FORM:SNP:PAR?", ":FORM:SNP:PAR %s",
        """Control the parameter format displayed in an SNP data file.

        Valid values are:

        =====   ===========================
        value   description
        =====   ===========================
        LINPH   Linear and Phase.
        LOGPH   Log and Phase.
        REIM    Real and Imaginary Numbers.
        =====   ===========================
        """,
        values=["LINPH", "LOGPH", "REIM"],
        validator=strict_discrete_set,
    )

    data_drawing_enabled = Instrument.control(
        "DD1?", "DD%d",
        """Control whether data drawing is enabled (True) or not (False). """,
        values={True: 1, False: 0},
        map_values=True,
    )

    event_status_enable_bits = Instrument.control(
        "*ESE?", "*ESE %d",
        """Control the Standard Event Status Enable Register bits.

        The register can be queried using the ~`query_event_status_register` method. Valid values
        are between 0 and 255. Refer to the instrument manual for an explanation of the bits.
        """,
        values=[0, 255],
        validator=strict_range,
        cast=int,
    )

    def query_event_status_register(self):
        """ Query the value of the Standard Event Status Register.

        Note that querying this value, clears the register. Refer to the instrument manual for an
        explanation of the returned value.
        """
        return self.values("*ESR?", cast=int)[0]

    service_request_enable_bits = Instrument.control(
        "*SRE?", "*SRE %d",
        """Control the Service Request Enable Register bits.

        Valid values are between 0 and 255; setting 0 performs a register reset. Refer to the
        instrument manual for an explanation of the bits.
        """,
        values=[0, 255],
        validator=strict_range,
        cast=int,
    )

    def return_to_local(self):
        """ Returns the instrument to local operation. """
        self.write("RTL")

    binary_data_byte_order = Instrument.control(
        ":FORM:BORD?", ":FORM:BORD %s",
        """Control the binary numeric I/O data byte order.

        valid values are:

        =====   =========================================
        value   description
        =====   =========================================
        NORM    The most significant byte (MSB) is first
        SWAP    The least significant byte (LSB) is first
        =====   =========================================
        """,
        values=["NORM", "SWAP"],
        validator=strict_discrete_set,
    )

    # TODO: use this value to determine the number of channels
    max_number_of_points = Instrument.control(
        ":SYST:POIN:MAX?", ":SYST:POIN:MAX %d",
        """Control the maximum number of points the instrument can measure in a sweep.

        Note that when this value is changed, the instrument will be rebooted.
        Valid values are 25000 and 100000. When 25000 points is selected, the instrument supports 16
        channels with 16 traces each; when 100000 is selected, the instrument supports 1 channel
        with 16 traces.
        """,
        values=[25000, 100000],
        validator=strict_discrete_set,
        cast=int,
    )

    number_of_channels = Instrument.control(
        ":DISP:COUN?", ":DISP:COUN %d",
        """Control the number of displayed (and therefore accessible) channels.

        When the system is in 25000 points mode, the number of channels can be 1, 2, 3, 4, 6, 8, 9,
        10, 12, or 16; when the system is in 100000 points mode, the system only supports 1 channel.
        If a value is provided that is not valid in the present mode, the instrument is set to the
        next higher channel number.
        """,
        values=[1, 16],
        validator=strict_range,
        cast=int,
    )

    DISPLAY_LAYOUTS = ["R1C1", "R1C2", "R2C1", "R1C3", "R3C1",
                       "R2C2C1", "R2C1C2", "C2R2R1", "C2R1R2",
                       "R1C4", "R4C1", "R2C2", "R2C3", "R3C2",
                       "R2C4", "R4C2", "R3C3", "R5C2", "R2C5",
                       "R4C3", "R3C4", "R4C4"]
    display_layout = Channel.control(
        ":DISP:SPL?", ":DISP:SPL %s",
        """Control the channel display layout in a Row-by-Column format.

        Valid values are: {}. The number
        following the R indicates the number of rows, following the C the number of columns.
        """.format(", ".join(DISPLAY_LAYOUTS)),
        values=DISPLAY_LAYOUTS,
        validator=strict_discrete_set,
        cast=int,
    )

    active_channel = Instrument.control(
        ":DISP:WIND:ACT?", ":DISP:WIND%d:ACT",
        """Control the active channel. """,
        values=CHANNELS,
        validator=strict_range,
        cast=int,
    )

    bandwidth_enhancer_enabled = Instrument.control(
        ":SENS:BAND:ENH?", ":SENS:BAND:ENH %d",
        """Control the state of the IF bandwidth enhancer. """,
        values={True: 1, False: 0},
        map_values=True,
    )

    trigger_source = Instrument.control(
        ":TRIG:SOUR?", ":TRIG:SOUR %s",
        """Control the source of the sweep/measurement triggering.

        Valid values are:

        =====   ==================================================
        value   description
        =====   ==================================================
        AUTO    Automatic triggering
        MAN     Manual triggering
        EXTT    Triggering from rear panel BNC via the GPIB parser
        EXT     External triggering port
        REM     Remote triggering
        =====   ==================================================
        """,
        values=["AUTO", "MAN", "EXTT", "EXT", "REM"],
        validator=strict_discrete_set,
    )

    external_trigger_type = Instrument.control(
        ":TRIG:EXT:TYP?", ":TRIG:EXT:TYP %s",
        """Control the type of trigger that will be associated with the external trigger.

        Valid values are POIN (for point), SWE (for sweep), CHAN (for channel), and ALL.
        """,
        values=TRIGGER_TYPES,
        validator=strict_discrete_set,
    )

    external_trigger_delay = Instrument.control(
        ":TRIG:EXT:DEL?", ":TRIG:EXT:DEL %g",
        """Control the the delay time of the external trigger.

        Valid values are between 0 [s] and 10[s] in steps of 1e-9 [s] (i.e. 1 ns).
        """,
        values=[0, 10],
        validator=strict_range,
    )

    external_trigger_edge = Instrument.control(
        ":TRIG:EXT:EDG?", ":TRIG:EXT:EDG %s",
        """Control the which edge is used for triggering of the external trigger.

        Valid values are POS (for positive or leading edge) or NEG (for negative or trailing edge).
        """,
        values=["POS", "NEG"],
        validator=strict_discrete_set,
    )

    external_trigger_handshake = Instrument.control(
        ":TRIG:EXT:HAND?", ":TRIG:EXT:HAND %s",
        """Control status of the external trigger handshake. """,
        values={True: 1, False: 0},
        map_values=True,
    )

    remote_trigger_type = Instrument.control(
        ":TRIG:REM:TYP?", ":TRIG:REM:TYP %s",
        """Control the type of trigger that will be associated with the remote trigger.

        Valid values are POIN (for point), SWE (for sweep), CHAN (for channel), and ALL.
        """,
        values=TRIGGER_TYPES,
        validator=strict_discrete_set,
    )

    manual_trigger_type = Instrument.control(
        ":TRIG:MAN:TYP?", ":TRIG:MAN:TYP %s",
        """Control the type of trigger that will be associated with the manual trigger.

        Valid values are POIN (for point), SWE (for sweep), CHAN (for channel), and ALL.
        """,
        values=TRIGGER_TYPES,
        validator=strict_discrete_set,
    )

    def trigger(self):
        """ Triggers a continuous sweep from the remote interface. """
        self.write("*TRG")

    def trigger_single(self):
        """ Triggers a single sweep with synchronization from the remote interface. """
        self.write(":TRIG:SING")

    def trigger_continuous(self):
        """ Triggers a continuous sweep from the remote interface. """
        self.write(":TRIG")

    hold_function_all_channels = Instrument.control(
        ":SENS:HOLD:FUNC?", ":SENS:HOLD:FUNC %s",
        """Control the hold function of all channels.

        Valid values are:

        =====   =================================================
        value   description
        =====   =================================================
        CONT    Perform continuous sweeps on all channels
        HOLD    Hold the sweep on all channels
        SING    Perform a single sweep and then hold all channels
        =====   =================================================
        """,
        values=["CONT", "HOLD", "SING"],
        validator=strict_discrete_set,
    )
