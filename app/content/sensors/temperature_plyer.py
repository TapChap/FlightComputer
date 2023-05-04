
from datetime import timedelta
from typing import Iterable, Tuple, Type, Union, cast
from typing_extensions import Self
from uuid import UUID
from app.logic.commands.command import Command
from app.content.general_commands.enable import DisableCommand, EnableCommand
from app.logic.rocket_definition import CommandBase, Part, Rocket
from plyer import temperature
from plyer.facades.temperature import Temperature



class PlyerTemperatureSensor(Part):

    type = 'Sensor.Temperature'

    enabled: bool = True

    # plyerSensor = Temperature()

    temperature_value: Union[float, None] = None

    sensor_failed: bool = False

    # Set update to only every 5 seconds as 
    # battery information is low frequency
    min_update_period = timedelta(milliseconds=10)
    min_measurement_period = timedelta(milliseconds=10)

    def __init__(self, _id: UUID, name: str, parent: Union[Part, Rocket, None], start_enabled = True):

        self.enabled = start_enabled
        self.try_enable_temperature(self.enabled)

        super().__init__(_id, name, parent, list()) # type: ignore

    def try_enable_temperature(self, enable: bool) -> bool:
        try:
            as_temperature = cast(Temperature, temperature)
            if enable:
                as_temperature.enable()
            else:
                as_temperature.disable()
        except Exception as e:
            self.sensor_failed = True
            print(f'Plyer temperature sensor failed: {e}')
            return False
    
        return True

    def get_accepted_commands(self) -> list[Type[CommandBase]]:
        return [EnableCommand, DisableCommand]
   
    def update(self, commands: Iterable[Command], now):
        
        for c in commands:
            if c is EnableCommand:
                self.enabled = True
            elif c is DisableCommand:
                self.enabled = False
            else:
                c.state = 'failed' # Part cannot handle this command
                continue
            
            c.state = 'success'
        
        if self.enabled and not self.sensor_failed:
            try:    
                as_temperature= cast(Temperature, temperature)
                self.temperature_value = as_temperature.temperature

            except Exception as e:
                print(f'Plyer temperature sensor failed: {e}')
                self.sensor_failed = True
        else:
            self.temperature_value = None
            
    def get_measurement_shape(self) -> Iterable[Tuple[str, Type]]:
        return [
            ('enabled', int),
            ('sensor_failed', int),
            ('temperature', float),
        ]

    def collect_measurements(self, now) -> Iterable[Iterable[Union[str, float, int, None]]]:
        return [[1 if self.enabled else 0, 1 if self.sensor_failed else 0, self.temperature_value]]
    
