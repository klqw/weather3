import re
import configparser
from datetime import datetime
from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import weather as w
import service

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "config.ini"
ERROR_PAGES = {
  403: {
    "title": "FORBIDDEN",
    "message": "このページにはアクセスできません。"
  },
  404: {
    "title": "NOT FOUND",
    "message": "お探しのページが見つかりませんでした。"
  },
  500: {
    "title": "INTERNAL SERVER ERROR",
    "message": "システム内でエラーが発生しました。"
  },
  503: {
    "title": "SERVICE UNAVAILABLE",
    "message": "ただいまサービスをご利用いただけません。"
  }
}

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

# root
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

# 都府県選択
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

# 地点選択
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

# 日付選択(別タブ)
@app.get("/weather/{station_type}/{block_no}/{date}")
def weather(
  request: Request,
  station_type: str,
  block_no: str,
  date: str
):
  # URLの簡易チェック
  if len(station_type) != 1 or len(block_no) > 10:
    raise HTTPException(status_code=404)
  
  if not re.fullmatch(r"\d{8}", date):
    raise HTTPException(status_code=404)

  try:
    datetime.strptime(date, "%Y%m%d")
  except ValueError:
    raise HTTPException(status_code=404)
  
  config = load_config()
  weather_data = w.get_weather_card(
    station_type,
    block_no,
    date,
    config
  )

  # 観測データを取得できなかった場合
  if weather_data is None:
    raise HTTPException(
      status_code=404,
      detail="weather_not_found"
    )

  observations = w.get_location_dates(
    station_type,
    block_no,
    config
  )

  available_dates = {
    row["observed_date"] for row in observations
  }
  navigation = service.get_navigation_dates(
    date,
    available_dates
  )

  return templates.TemplateResponse(
    request=request,
    name="weather.html",
    context={
      "weather": weather_data,
      "station_type": station_type,
      "block_no": block_no,
      "navigation": navigation
    }
  )

# 日付選択(SPA)
@app.get("/api/weather/{station_type}/{block_no}/{date}")
def get_weather_api(
  station_type: str,
  block_no: str,
  date: str
):
  config = load_config()

  return w.get_weather_card(
    station_type,
    block_no,
    date,
    config
  )

"""
極値表示
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

# エラーページ
def render_error_page(request, status_code, variant=None):
  error = ERROR_PAGES[status_code]

  error_title = error["title"]
  error_message = error["message"]

  if variant == "no-data":
    error_title = "NO DATA"
    error_message = "観測データは見つかりませんでした。"

  return templates.TemplateResponse(
    request=request,
    name="error.html",
    context={
      "status_code": status_code,
      "error_title": error_title,
      "error_message": error_message,
      "error_variant": variant
    },
    status_code=status_code
  )

# 別タブ
# 403 / 404 / 503
@app.exception_handler(403)
@app.exception_handler(404)
@app.exception_handler(503)
async def not_found_handler(request: Request, exc):
  status_code = exc.status_code

  if request.url.path.startswith("/api/"):
    return JSONResponse(
      status_code=status_code,
      content={"detail": str(exc.detail)},
      headers=getattr(exc, "headers", None)
    )

  error_variant = (
    "no-data"
    if status_code == 404
    and exc.detail == "weather_not_found"
    else None
  )

  return render_error_page(request, status_code, variant=error_variant)

# 500
@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
  if request.url.path.startswith("/api/"):
    return JSONResponse(
      status_code=500,
      content={"detail": "Internal Server Error"}
    )

  return render_error_page(request, 500)

# SPA
@app.get("/error/{status_code}")
def error_page(request: Request, status_code: int):
  if status_code not in ERROR_PAGES:
    raise HTTPException(status_code=404)
  return render_error_page(request, status_code)
