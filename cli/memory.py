"""Radijator memory channel model (driver-agnostic)."""

from chirp.chirp_common import Memory, PowerLevel


class RadijatorMemory:
    number: int = None
    name: str = None
    freq: int = None
    power_level: PowerLevel = None
    tone: str = None  # CHIRP tmode: "", "Tone", "TSQL", "DTCS", "DTCS-R", "TSQL-R", "Cross"
    rdcs_code: int = None
    tdcs_code: int = None
    dcs_polarity: int = None
    mode: str = None
    tuning_step: float = None
    duplex: str = None
    offset: int = None
    rtone: float = None
    ctone: float = None
    ptt_id: bool = None

    def __init__(
        self,
        number: int,
        name: str,
        freq: int,
        power_level: PowerLevel,
        tone: str = "",
        rdcs_code: int = 23,
        tdcs_code: int = 23,
        dcs_polarity: str = "NN",
        mode: str = "NFM",
        tuning_step: float = 5.0,
        duplex: str = "",
        offset: int = 0,
        rtone: float = 88.5,
        ctone: float = 88.5,
        ptt_id: bool = False,
    ):
        self.number = number
        self.name = name
        self.freq = freq
        self.power_level = power_level
        self.tone = tone
        self.rdcs_code = rdcs_code
        self.tdcs_code = tdcs_code
        self.dcs_polarity = dcs_polarity
        self.mode = mode
        self.tuning_step = tuning_step
        self.duplex = duplex
        self.offset = offset
        self.rtone = rtone
        self.ctone = ctone
        self.ptt_id = ptt_id

    def __str__(self):
        return f"Mem#{self.number} {self.name} Freq:{self.freq} Power:{self.power_level} RDCS:{self.rdcs_code} TDCS:{self.tdcs_code} DCS Polarity:{self.dcs_polarity}"

    @staticmethod
    def from_chirp_memory(mem: Memory) -> "RadijatorMemory":
        return RadijatorMemory(
            number=mem.number,
            name=mem.name,
            freq=mem.freq,
            power_level=mem.power,
            tone=mem.tmode,
            rdcs_code=mem.rx_dtcs,
            tdcs_code=mem.dtcs,
            dcs_polarity=mem.dtcs_polarity,
            mode=mem.mode,
            tuning_step=mem.tuning_step,
            duplex=mem.duplex,
            offset=mem.offset,
            rtone=mem.rtone,
            ctone=mem.ctone,
        )

    @staticmethod
    def to_chirp_memory(rad_mem: "RadijatorMemory") -> Memory:
        mem = Memory()
        mem.number = rad_mem.number
        mem.name = rad_mem.name
        mem.freq = rad_mem.freq
        mem.power = rad_mem.power_level
        mem.tmode = rad_mem.tone
        mem.rtone = rad_mem.rtone
        mem.ctone = rad_mem.ctone
        mem.rx_dtcs = rad_mem.rdcs_code
        mem.dtcs = rad_mem.tdcs_code
        mem.dtcs_polarity = rad_mem.dcs_polarity
        mem.mode = rad_mem.mode
        mem.tuning_step = rad_mem.tuning_step
        mem.duplex = rad_mem.duplex
        mem.offset = rad_mem.offset
        mem.empty = False
        return mem

    @staticmethod
    def from_json(data: dict, power_level: PowerLevel) -> "RadijatorMemory":
        return RadijatorMemory(
            number=data.get("number", None),
            name=data["name"],
            freq=data["frequency"],
            power_level=power_level,
            tone=data.get("tone", ""),
            rdcs_code=data.get("rdcs_code", 23),
            tdcs_code=data.get("tdcs_code", 23),
            dcs_polarity=data.get("dcs_polarity", "NN"),
            mode=data.get("mode", "NFM"),
            tuning_step=data.get("tuning_step", 5.0),
            duplex=data.get("duplex", ""),
            offset=data.get("offset", 0),
            rtone=data.get("rtone", 88.5),
            ctone=data.get("ctone", 88.5),
            ptt_id=data.get("ptt_id", False),
        )
