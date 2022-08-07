from __future__ import annotations

from datetime import timedelta
from typing import Any

import reactivex.operators as ops
from homeassistant.components.sensor import (SensorDeviceClass, SensorEntity,
                                             SensorStateClass)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ELECTRIC_CURRENT_AMPERE,
                                 ELECTRIC_POTENTIAL_VOLT, ENERGY_WATT_HOUR,
                                 FREQUENCY_HERTZ, PERCENTAGE, POWER_WATT,
                                 TEMP_CELSIUS)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import utcnow
from reactivex import Observable

from . import DOMAIN, EcoFlowDevice, EcoFlowEntity, select_bms
from .ecoflow import (is_delta, is_delta_mini, is_delta_pro, is_power_station,
                      is_river)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    device: EcoFlowDevice = hass.data[DOMAIN][entry.entry_id]
    entities = []

    if is_power_station(device.product):
        entities.extend([
            CurrentEntity(device, device.inverter,
                          "ac_in_current", "AC input current"),
            CurrentEntity(device, device.inverter,
                          "ac_out_current", "AC output current"),
            EnergyEntity(device, device.pd, "ac_in_energy",
                         "AC input energy"),
            EnergyEntity(device, device.pd, "ac_out_energy",
                         "AC output energy"),
            EnergyEntity(device, device.pd, "car_in_energy",
                         "Car input energy"),
            EnergyEntity(device, device.pd, "dc_out_energy",
                         "DC output energy"),
            EnergyEntity(device, device.pd, "mppt_in_energy",
                         "MPPT input energy"),
            FanEntity(device, device.inverter, "fan_state", "Fan"),
            FrequencyEntity(device, device.inverter,
                            "ac_in_freq", "AC input frequency"),
            FrequencyEntity(device, device.inverter,
                            "ac_out_freq", "AC output frequency"),
            RemainEntity(device, device.pd, "remain_display", "Remain"),
            LevelEntity(device, device.pd, "battery_level",
                        "Battery"),
            VoltageEntity(device, device.inverter,
                          "ac_in_voltage", "AC input voltage"),
            VoltageEntity(device, device.inverter,
                          "ac_out_voltage", "AC output voltage"),
            WattsEntity(device, device.pd, "in_power", "Total input"),
            WattsEntity(device, device.pd, "out_power", "Total output"),
            WattsEntity(device, device.inverter,
                        "ac_consumption", "AC output + loss", real=True),
            WattsEntity(device, device.inverter, "ac_out_power",
                        "AC output", real=False),
            WattsEntity(device, device.pd, "usb_out1_power",
                        "USB-A left output"),
            WattsEntity(device, device.pd, "usb_out2_power",
                        "USB-A right output"),
        ])
        if is_delta(device.product):
            bms = (
                device.bms.pipe(select_bms(0), ops.share()),
                device.bms.pipe(select_bms(1), ops.share()),
                device.bms.pipe(select_bms(2), ops.share()),
            )
            entities.extend([
                CurrentEntity(device, device.mppt, "dc_in_current",
                              "DC input current"),
                CyclesEntity(
                    device, bms[0], "battery_cycles", "Main battery cycles", 0),
                RemainEntity(device, device.ems,
                             "battery_remain_charge", "Remain charge"),
                RemainEntity(device, device.ems,
                             "battery_remain_discharge", "Remain discharge"),
                SingleLevelEntity(
                    device, bms[0], "battery_level_f32", "Main battery", 0),
                TempEntity(device, device.inverter, "ac_out_temp",
                           "AC temperature"),
                TempEntity(device, bms[0], "battery_temp",
                           "Main battery temperature", 0),
                TempEntity(device, device.mppt, "dc_in_temp",
                           "DC input temperature"),
                TempEntity(device, device.mppt, "dc24_temp",
                           "DC output temperature"),
                TempEntity(device, device.pd, "typec_out1_temp",
                           "USB-C left temperature"),
                TempEntity(device, device.pd, "typec_out2_temp",
                           "USB-C right temperature"),
                VoltageEntity(device, device.mppt, "dc_in_voltage",
                              "DC input voltage"),
                WattsEntity(device, device.inverter,
                            "ac_in_power", "AC input"),
                WattsEntity(device, device.mppt, "dc_in_power",
                            "DC input", real=True),
                WattsEntity(device, device.mppt,
                            "car_consumption", "Car output + loss", real=True),
                WattsEntity(device, device.mppt,
                            "car_out_power", "Car output"),
            ])
            if is_delta_mini(device.product):
                entities.extend([
                    WattsEntity(device, device.pd,
                                "usbqc_out1_power", "USB-Fast output"),
                    WattsEntity(device, device.pd,
                                "typec_out1_power", "USB-C output"),
                ])
            else:
                entities.extend([
                    CyclesEntity(
                        device, bms[1], "battery_cycles", "Extra1 battery cycles", 1),
                    CyclesEntity(
                        device, bms[2], "battery_cycles", "Extra2 battery cycles", 2),
                    SingleLevelEntity(
                        device, bms[1], "battery_level_f32", "Extra1 battery", 1),
                    SingleLevelEntity(
                        device, bms[2], "battery_level_f32", "Extra2 battery", 2),
                    TempEntity(device, bms[1], "battery_temp",
                               "Extra1 battery temperature", 1),
                    TempEntity(device, bms[2], "battery_temp",
                               "Extra2 battery temperature", 2),
                    WattsEntity(device, device.pd, "usbqc_out1_power",
                                "USB-Fast left output"),
                    WattsEntity(device, device.pd, "usbqc_out2_power",
                                "USB-Fast right output"),
                    WattsEntity(device, device.pd, "typec_out1_power",
                                "USB-C left output"),
                    WattsEntity(device, device.pd, "typec_out2_power",
                                "USB-C right output"),
                ])
            if is_delta_pro(device.product):
                entities.extend([
                    WattsEntity(device, device.mppt,
                                "anderson_out_power", "Anderson output"),
                ])
        if is_river(device.product):
            extra = device.bms.pipe(select_bms(1), ops.share())
            entities.extend([
                CurrentEntity(device, device.inverter, "dc_in_current",
                              "DC input current"),
                CyclesEntity(device, device.ems, "battery_cycles",
                             "Main battery cycles"),
                CyclesEntity(device, extra, "battery_cycles",
                             "Extra battery cycles", 1),
                SingleLevelEntity(device, device.ems, "battery_main_level",
                            "Main battery"),
                SingleLevelEntity(
                    device, extra, "battery_level", "Extra battery", 1),
                TempEntity(device, device.inverter, "ac_in_temp",
                           "AC input temperature"),
                TempEntity(device, device.inverter, "ac_out_temp",
                           "AC output temperature"),
                TempEntity(device, device.ems, "battery_main_temp",
                           "Main battery temperature"),
                TempEntity(device, extra, "battery_temp",
                           "Extra battery temperature", 1),
                TempEntity(device, device.pd, "car_out_temp",
                           "DC output temperature"),
                TempEntity(device, device.pd, "typec_out1_temp",
                           "USB-C temperature"),
                VoltageEntity(device, device.inverter, "dc_in_voltage",
                              "DC input voltage"),
                WattsEntity(device, device.pd, "car_out_power", "Car output"),
                WattsEntity(device, device.pd, "light_power", "Light output"),
                WattsEntity(device, device.pd, "usbqc_out1_power",
                            "USB-Fast output"),
                WattsEntity(device, device.pd, "typec_out1_power",
                            "USB-C output"),
            ])

    async_add_entities(entities)


class BaseEntity(SensorEntity, EcoFlowEntity):
    def _on_updated(self, data: dict[str, Any]):
        self._attr_native_value = data[self._key]


class CurrentEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = ELECTRIC_CURRENT_AMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT


class CyclesEntity(BaseEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:battery-heart-variant"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING


class EnergyEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = ENERGY_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING


class FanEntity(BaseEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def icon(self):
        value = self.native_value
        if value is None or self.native_value <= 0:
            return "mdi:fan-off"
        return "mdi:fan"


class FrequencyEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = FREQUENCY_HERTZ
    _attr_state_class = SensorStateClass.MEASUREMENT


class LevelEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device: EcoFlowDevice, src: Observable[dict[str, Any]], key: str, name: str, bms_id: int | None = None):
        super().__init__(device, src, key, name, bms_id)
        self._attr_extra_state_attributes = {}


class RemainEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_registry_enabled_default = False

    def _on_updated(self, data: dict[str, Any]):
        value: timedelta = data[self._key]
        if value.total_seconds() == 8639940:
            self._attr_native_value = None
        else:
            self._attr_native_value = utcnow() + value


class SingleLevelEntity(LevelEntity):
    def _on_updated(self, data: dict[str, Any]):
        super()._on_updated(data)
        if "battery_capacity_remain" in data:
            self._attr_extra_state_attributes["capacity_remain"] = data["battery_capacity_remain"]
        if "battery_capacity_full" in data:
            self._attr_extra_state_attributes["capacity_full"] = data["battery_capacity_full"]
        if "battery_capacity_design" in data:
            self._attr_extra_state_attributes["capacity_design"] = data["battery_capacity_design"]


class TempEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT


class VoltageEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = ELECTRIC_POTENTIAL_VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT


class WattsEntity(BaseEntity):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = POWER_WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device: EcoFlowDevice, src: Observable[dict[str, Any]], key: str, name: str, real: bool | int = False):
        super().__init__(device, src, key, name)
        if key.endswith("_consumption"):
            self._key = key[:-11] + "out_power"
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._real = real

    def _on_updated(self, data: dict[str, Any]):
        key = self._key[:-5]
        if self._real is not False and f"{key}current" in data and f"{key}voltage" in data:
            self._attr_native_value = (
                data[f"{key}current"] * data[f"{key}voltage"])
            if self._real is not True:
                self._attr_native_value = round(
                    self._attr_native_value, self._real)
                if self._real == 0:
                    self._attr_native_value = int(self._attr_native_value)
        else:
            super()._on_updated(data)
