from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MachineState(BaseModel):
    state: str
    substate: str


class MachineSnapshot(BaseModel):
    timestamp: datetime
    state: MachineState
    flow: float
    pressure: float
    targetFlow: float
    targetPressure: float
    mixTemperature: float
    groupTemperature: float
    targetMixTemperature: float
    targetGroupTemperature: float
    profileFrame: int
    steamTemperature: int | None = None


class ScaleSnapshot(BaseModel):
    timestamp: datetime
    weight: float
    weightFlow: float
    battery: int | None = None


class Measurement(BaseModel):
    elapsed: float
    machine: MachineSnapshot
    scale: ScaleSnapshot | None = None
    volume: float | None = None


class WorkflowContext(BaseModel):
    targetDoseWeight: float | None = None
    targetYield: float | None = None
    grinderId: str | None = None
    grinderModel: str | None = None
    grinderSetting: str | None = None
    beanBatchId: str | None = None
    coffeeName: str | None = None
    coffeeRoaster: str | None = None
    finalBeverageType: str | None = None
    baristaName: str | None = None
    drinkerName: str | None = None
    extras: dict[str, Any] | None = None


class SteamSettings(BaseModel):
    targetTemperature: int | None = None
    duration: int | None = None
    flow: float | None = None
    stopAtTemperature: float | None = None


class HotWaterData(BaseModel):
    targetTemperature: int | None = None
    duration: int | None = None
    volume: int | None = None
    flow: float | None = None


class RinseData(BaseModel):
    targetTemperature: int | None = None
    duration: int | None = None
    flow: float | None = None


class Workflow(BaseModel):
    id: str
    name: str
    description: str | None = None
    profile: dict[str, Any]
    context: WorkflowContext | None = None
    steamSettings: SteamSettings | None = None
    hotWaterData: HotWaterData | None = None
    rinseData: RinseData | None = None


class Annotations(BaseModel):
    espressoNotes: str | None = None
    grindNotes: str | None = None
    drinkNotes: str | None = None
    extras: dict[str, Any] | None = None


class ShotUpload(BaseModel):
    id: str
    timestamp: datetime
    duration: float = Field(ge=0)
    measurements: list[Measurement]
    workflow: Workflow
    annotations: Annotations | None = None


class ShotUploadCreate(BaseModel):
    timestamp: datetime
    duration: float = Field(ge=0)
    measurements: list[Measurement]
    workflow: Workflow
    annotations: Annotations | None = None


class ShotUploadUpdate(BaseModel):
    timestamp: datetime | None = None
    duration: float | None = Field(default=None, ge=0)
    measurements: list[Measurement] | None = None
    workflow: Workflow | None = None
    annotations: Annotations | None = None
