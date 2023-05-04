
from datetime import timedelta
from typing import Iterable, Tuple, Type, Union, cast
from typing_extensions import Self
from uuid import UUID
from app.logic.commands.command import Command
from app.content.general_commands.enable import DisableCommand, EnableCommand
from app.logic.rocket_definition import CommandBase, Part, Rocket
from plyer import spatialorientation
from plyer.facades.spatialorientation import SpatialOrientation


class PlyerSpatialOrientationSensor(Part):

    type = 'Sensor.SpatialOrientation'

    enabled: bool = True

    # plyerSensor = SpatialOrientation()

    sensor_failed: bool = False

    spatial_orientation: Union[None, Tuple[float, float, float], Tuple[None, None, None]]

    min_update_period = timedelta(milliseconds=1)

    min_measurement_period = timedelta(milliseconds=1)

    def __init__(self, _id: UUID, name: str, parent: Union[Part, Rocket, None], start_enabled = True):

        self.enabled = start_enabled
        self.try_enable_spatial_orientation(self.enabled)

        super().__init__(_id, name, parent, list()) # type: ignore

    def get_accepted_commands(self) -> list[Type[CommandBase]]:
        return [EnableCommand, DisableCommand]
    
    def try_enable_spatial_orientation(self, enable: bool) -> bool:
        try:
            as_spatial_orientation = cast(SpatialOrientation, spatialorientation)
            if enable:
                as_spatial_orientation.enable_listener()
            else:
                as_spatial_orientation.disable_listener()
        except Exception as e:
            self.sensor_failed = True
            print(f'Plyer spatial orientation sensor failed: {e}')
            return False
    
        return True
   
    def update(self, commands: Iterable[Command], now):
        
        for c in commands:
            if c is EnableCommand:
                self.enabled = True
                c.state = 'success' if self.try_enable_spatial_orientation(True) else 'failed'
            elif c is DisableCommand:
                self.enabled = False
                c.state = 'success' if self.try_enable_spatial_orientation(False) else 'failed'
            else:
                c.state = 'failed' # Part cannot handle this command
                continue
            
        
        if self.enabled and not self.sensor_failed:
            try:    
                as_spatial_orientation = cast(SpatialOrientation, spatialorientation)
                self.spatial_orientation = as_spatial_orientation.orientation
            except Exception as e:
                print(f'Plyer spatial orientation sensor failed: {e}')
                self.sensor_failed = True
        else:
            self.spatial_orientation = None
            
    def get_measurement_shape(self) -> Iterable[Tuple[str, Type]]:
        return [
            ('enabled', int),
            ('sensor_failed', int),
            ('spatial_orientation-z', float),
            ('spatial_orientation-x', float),
            ('spatial_orientation-y', float),
        ]

    def collect_measurements(self, now) -> Iterable[Iterable[Union[str, float, int, None]]]:
        spat =  self.spatial_orientation or [None, None, None]
        return [[1 if self.enabled else 0, 1 if self.sensor_failed else 0, spat[0], spat[1], spat[2]]]
    
