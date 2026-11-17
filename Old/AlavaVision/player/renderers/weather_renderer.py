"""WeatherRenderer - displays weather information fetching from OpenWeatherMap."""

import json
import urllib.request
import urllib.error
from datetime import datetime
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont
from player.renderers.base_renderer import BaseRenderer
from core.widgets.weather_widget import WeatherWidget
from core.services.log_service import LogService
from core.services.config_service import ConfigService


class WeatherRenderer(BaseRenderer):
    """Renderer for weather widget - fetches and displays weather data."""

    def __init__(self, widget: WeatherWidget, parent: QWidget | None = None) -> None:
        super().__init__(widget, parent)
        self._log = LogService()
        self._config = ConfigService()
        self._timer: QTimer | None = None
        self._temp_label: QLabel | None = None
        self._desc_label: QLabel | None = None
        self._city_label: QLabel | None = None
        self._icon_label: QLabel | None = None

    def create_ui(self) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background-color: #0a0a2e;")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        self._city_label = QLabel()
        self._city_label.setAlignment(Qt.AlignCenter)
        self._city_label.setStyleSheet("color: #a0a0ff; font-size: 24px; font-weight: bold;")
        layout.addWidget(self._city_label)

        # Icon + temp row
        info_layout = QHBoxLayout()
        info_layout.setAlignment(Qt.AlignCenter)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(80, 80)
        info_layout.addWidget(self._icon_label)

        self._temp_label = QLabel()
        self._temp_label.setStyleSheet("color: #ffffff; font-size: 56px; font-weight: bold;")
        info_layout.addWidget(self._temp_label)

        layout.addLayout(info_layout)

        self._desc_label = QLabel()
        self._desc_label.setAlignment(Qt.AlignCenter)
        self._desc_label.setStyleSheet("color: #c0c0c0; font-size: 18px;")
        layout.addWidget(self._desc_label)

        return container

    def start(self) -> None:
        self._fetch_weather()
        interval = self.widget.get_update_interval() * 1000
        self._timer = QTimer()
        self._timer.timeout.connect(self._fetch_weather)
        self._timer.start(interval)

    def _fetch_weather(self) -> None:
        api_key = self._config.get("OPENWEATHER_API_KEY", "")
        if not api_key:
            if self._city_label:
                self._city_label.setText("API key não configurada")
            return

        city = self.widget.get_city()
        unit = self.widget.get_unit()
        unit_param = "metric" if unit == "celsius" else "imperial"
        unit_symbol = "°C" if unit == "celsius" else "°F"

        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={urllib.parse.quote(city)}&units={unit_param}&appid={api_key}"
        )

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AlavaVision/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            if self._city_label:
                self._city_label.setText(data.get("name", city))
            if self._temp_label:
                temp = round(data["main"]["temp"])
                self._temp_label.setText(f"{temp}{unit_symbol}")
            if self._desc_label:
                desc = data["weather"][0]["description"].capitalize()
                self._desc_label.setText(desc)

            self._log.info(
                f"Weather fetched for {city}: {data['main']['temp']}{unit_symbol}",
                source="player", category="weather",
            )

        except urllib.error.HTTPError as e:
            if e.code == 401:
                self._log.error("Invalid OpenWeatherMap API key", source="player", category="weather")
            elif e.code == 404:
                self._log.error(f"City not found: {city}", source="player", category="weather")
        except Exception as e:
            self._log.error(f"Weather fetch error: {e}", source="player", category="weather")

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None