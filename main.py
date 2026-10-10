import configparser
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
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

@app.get("/api/locations/{prec_no}")
def api_locatoins(prec_no: str):
  config = load_config()
  return w.get_locations(
    prec_no,
    config
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

"""
metric: 
  avg_temp, max_temp, min_temp,
  avg_humidity, sunshine_hours, avg_wind_speed,
  precipitation, max_snow_dept
comparison:
  loc_day, loc_mon, loc_all,
  all_day, all_mon, all_all
extreme:
  max, min
"""
@app.get("/api/extremes/{metric}/{comparison}/{extreme}/{location_id}/{date}")
def get_extremes(
  metric: str,
  comparison: str,
  extreme: str,
  location_id: int,
  date: str
):
  config = load_config()
  observed_date = datetime.strptime(date, "%Y%m%d").date()

  return w.get_extreme_records(
    config,
    metric,
    comparison,
    extreme,
    location_id,
    observed_date
  )