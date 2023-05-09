
import asyncio
from datetime import datetime, timedelta
from random import random
from typing import Collection, Iterable, Sequence, Tuple, Union, cast
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from plyer.facades.accelerometer import Accelerometer
from kivy.core.window import Window
from plyer import accelerometer
from uuid import uuid4
from app.flight_executer import FlightExecuter
from app.logic.commands.command import Command
from app.logic.execution import topological_sort
from app.logic.measurement_sink import ApiMeasurementSinkBase, MeasurementSinkBase, MeasurementsByPart
from app.logic.rocket_definition import Measurements, Part
from app.models.flight_measurement import FlightMeasurement, FlightMeasurementSchema
from app.rockets.make_spatula import make_spatula
from app.models.flight import Flight
from app.models.command import Command as CommandModel
from app.logic.rocket_definition import Rocket
from datetime import datetime
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class FlightCreator(BoxLayout):

    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        super().__init__(**kwargs)

        self.creation_complete_future = asyncio.Future()

        self.flight_name_input = TextInput(text=f'Flight {datetime.now().isoformat()}')
        self.add_widget(self.flight_name_input)

        self.create_btn = Button(text='Create Flight')
        self.create_btn.bind(on_press = self.make_create_flight_callback()) # type: ignore
        self.add_widget(self.create_btn)

    def make_create_flight_callback(self):
        def create_flight(instance):
            self.creation_complete_future.set_result({'name': self.flight_name_input.text})
        return create_flight

class RSSFlightComputer(App):

    label = None

    def build(self):

        # request_permissions([Permission.HIGH_SAMPLING_RATE_SENSORS])

        self.root_layout = BoxLayout(orientation='vertical')

        return self.root_layout

app = RSSFlightComputer()

def init_app():
    return app, run_loop

async def run_loop():

    while(True):
        flight_creator = FlightCreator()
        app.root_layout.add_widget(flight_creator)

        create_result = await flight_creator.creation_complete_future

        app.root_layout.remove_widget(flight_creator)

        flight_config = make_spatula()

        flight_config.name = create_result['name']

        if flight_config.should_add_default_uis:
            flight_config.add_default_uis()

        flight_executor = FlightExecuter(flight_config)
        app.root_layout.add_widget(flight_executor.ui)

        # Wait for the flight to finish or crash
        await flight_executor.control_loop_task

        app.root_layout.remove_widget(flight_executor.ui)


