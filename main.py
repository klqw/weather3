import configparser
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
# from weather import get_prefectures
# from weather import get_locations
# from weather import get_location_dates
# from weather import get_weather_card
import weather as w

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "config.ini"

# --------------------
# 設定ファイル
# --------------------
def load_config():
  config = configparser.ConfigParser()
  config.read(CONFIG_FILE, encoding="utf-8")
  return config


# --------------------
# FastAPI
# --------------------
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount(
  "/static",
  StaticFiles(directory="static"),
  name="static"
)

@app.get("/")
def index(request: Request):
  config = load_config()
  prefectures = w.get_prefectures(config)

  return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={
      "prefectures": prefectures
    }
  )

@app.get("/api/prefectures")
def api_prefectures():
  config = load_config()
  return w.get_prefectures(config)

@app.get("/prefecture/{prec_no}/")
def locations(
  request: Request,
  prec_no: str
):
  config = load_config()
  locations = w.get_locations(
    prec_no,
    config
  )

  return templates.TemplateResponse(
    request=request,
    name="locations.html",
    context={
      "locations": locations
    }
  )

@app.get("/api/locations/{prec_no}")
def api_locatoins(prec_no: str):
  config = load_config()
  return w.get_locations(
    prec_no,
    config
  )

@app.get("/location/{station_type}/{block_no}")
def location_dates(
  request: Request,
  station_type: str,
  block_no: str
):
  config = load_config()
  observations = w.get_location_dates(
    station_type,
    block_no,
    config
  )
  observation_dates = [
    row["observed_date"].isoformat()
    for row in observations
  ]

  return templates.TemplateResponse(
    request=request,
    name="location_dates.html",
    context={
      "station_type": station_type,
      "block_no": block_no,
      "observations": observations,
      "observation_dates": observation_dates
    }
  )

@app.get("/api/location/{station_type}/{block_no}/dates")
def api_location_dates(station_type: str, block_no: str):
  config = load_config()
  rows = w.get_location_dates(
    station_type,
    block_no,
    config
  )

  return [
    row["observed_date"]
    for row in rows
  ]

@app.get("/weather/{station_type}/{block_no}/{date}")
def weather(
  request: Request,
  station_type: str,
  block_no: str,
  date: str
):
  config = load_config()
  weather_data = w.get_weather_card(
    station_type,
    block_no,
    date,
    config
  )

  return templates.TemplateResponse(
    request=request,
    name="weather.html",
    context={
      "weather": weather_data
    }
  )
