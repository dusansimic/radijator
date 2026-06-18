"""Concrete RadijatorRadio subclasses, one per supported radio family.

Importing this module populates `cli.radio.RADIO_MODEL_ID_CLASS_DICT`
via the @register_radio decorator side effect."""

from chirp.chirp_common import Memory
from chirp.drivers.uv5r import BaofengUV5R, BaofengUV82Radio
from chirp.drivers.uv5r import PTTID_LIST as UV5R_PTTID_LIST
from chirp.drivers.uv6r import UV6R
from chirp.drivers.baofeng_wp970i import UV9R
from chirp.drivers.baofeng_uv17Pro import UV25, BFK5Plus, UV5RMini, UV21ProV2
from chirp.drivers.mml_jc8810 import RT470XRadio, RT470Radio
from chirp.drivers.radtel_rt900 import RT900BT
from chirp.settings import (
    RadioSetting,
    RadioSettingGroup,
    RadioSettingValueList,
)

from .memory import RadijatorMemory
from .radio import RadijatorRadio, register_radio


@register_radio
class RadijatorUV5R(RadijatorRadio):
    """
    Supported models:
    - Baofeng UV-5R
    - Baofeng UV-5R Plus
    - Baofeng UV-5RA
    """

    DRIVER_CLASS = BaofengUV5R
    RADIJATOR_SETTINGS_PROFILE_ID = "uv5r"
    RESET_TIME = 6
    DTMF_SETTING_NAME = "pttid/0.code"
    POWERON_MSG_WIDTH = 7

    def set_dtmf_code(self, code: str, log_fn=print):
        if self._settings is None:
            raise RuntimeError("download settings before setting DTMF code")
        targets = {
            self.DTMF_SETTING_NAME: code,
            # DT+ANI keys both DTMF and ANI sidetones on PTT, otherwise
            # the radio writes the code internally but never transmits it.
            "dtmfst": "DT+ANI",
        }
        found = set()
        for setting in self._settings.walk():
            name = setting.get_name()
            if name in targets:
                setting.__setitem__(0, targets[name])
                found.add(name)
        missing = set(targets) - found
        if missing:
            raise RuntimeError(f"DTMF settings not found in radio settings: {missing}")
        log_fn(f"DTMF slot 1 set to {code}; sidetone set to DT+ANI")
        self.radio.set_settings(self._settings)
        self._settings = self.radio.get_settings()

    def _apply_memory_extras(self, chirp_mem: Memory, rad_mem: RadijatorMemory):
        if not rad_mem.ptt_id:
            return
        chirp_mem.extra = RadioSettingGroup("Extra", "extra")
        chirp_mem.extra.append(
            RadioSetting(
                "pttid",
                "PTT ID",
                RadioSettingValueList(
                    UV5R_PTTID_LIST,
                    current_index=UV5R_PTTID_LIST.index("BOT"),
                ),
            )
        )

    def set_power_on_message(self, line1: str, line2: str, log_fn=print):
        if self._settings is None:
            raise RuntimeError("download settings before setting power-on message")
        targets = {
            "poweron_msg.line1": line1,
            "poweron_msg.line2": line2,
            "ponmsg": "Message",
        }
        found = set()
        for setting in self._settings.walk():
            name = setting.get_name()
            if name in targets:
                setting.__setitem__(0, targets[name])
                found.add(name)
        missing = set(targets) - found
        if missing:
            raise RuntimeError(
                f"power-on message settings not found in radio settings: {missing}"
            )
        log_fn(f"Power-on message: {line1!r} / {line2!r}")
        self.radio.set_settings(self._settings)
        self._settings = self.radio.get_settings()


# TODO: Add to profile
@register_radio
class RadijatorUV6R(RadijatorRadio):
    DRIVER_CLASS = UV6R
    RADIJATOR_SETTINGS_PROFILE_ID = "uv6r"
    RESET_TIME = 6


# TODO: Check if it works
# TODO: Add to profile
class RadijatorUV9R(RadijatorRadio):
    DRIVER_CLASS = UV9R
    RADIJATOR_SETTINGS_PROFILE_ID = "uv9r"
    RESET_TIME = 6


@register_radio
class RadijatorUV82(RadijatorRadio):
    DRIVER_CLASS = BaofengUV82Radio
    RADIJATOR_SETTINGS_PROFILE_ID = "uv82"
    RESET_TIME = 6


@register_radio
class RadijatorUV25(RadijatorRadio):
    DRIVER_CLASS = UV25
    RADIJATOR_SETTINGS_PROFILE_ID = "uv25"
    RESET_TIME = 4


@register_radio
class RadijatorUV5RMini(RadijatorRadio):
    DRIVER_CLASS = UV5RMini
    RADIJATOR_SETTINGS_PROFILE_ID = "uv5rmini"
    RESET_TIME = 4


@register_radio
class RadijatorUV21Pro(RadijatorRadio):
    DRIVER_CLASS = UV21ProV2
    RADIJATOR_SETTINGS_PROFILE_ID = "uv21pro"
    RESET_TIME = 4


# TODO: Fix issue with exception when logging
# TODO: Add to profile
class RadijatorK5Plus(RadijatorRadio):
    DRIVER_CLASS = BFK5Plus
    RADIJATOR_SETTINGS_PROFILE_ID = "k5plus"
    RESET_TIME = 4


# TODO: Baofeng UV-17 variants


@register_radio
class RadijatorRT470X(RadijatorRadio):
    DRIVER_CLASS = RT470XRadio
    RADIJATOR_SETTINGS_PROFILE_ID = "rt470x"
    RESET_TIME = 3


@register_radio
class RadijatorRT470(RadijatorRadio):
    DRIVER_CLASS = RT470Radio
    RADIJATOR_SETTINGS_PROFILE_ID = "rt470"
    RESET_TIME = 3


# TODO: Fix issue with exception when logging
# TODO: Add to profile
@register_radio
class RadijatorRT900BT(RadijatorRadio):
    DRIVER_CLASS = RT900BT
    RADIJATOR_SETTINGS_PROFILE_ID = "rt900bt"
    RESET_TIME = 5
