"""Widget definitions and base class."""
from core.widgets.base_widget import BaseWidget
from core.widgets.site_widget import SiteWidget
from core.widgets.image_widget import ImageWidget
from core.widgets.text_widget import TextWidget
from core.widgets.clock_widget import ClockWidget
from core.widgets.pdf_widget import PDFWidget
from core.widgets.weather_widget import WeatherWidget

__all__ = [
    "BaseWidget",
    "SiteWidget",
    "ImageWidget",
    "TextWidget",
    "ClockWidget",
    "PDFWidget",
    "WeatherWidget",
]