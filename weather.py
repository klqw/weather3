import configparser
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from db import get_connection
from psycopg.rows import dict_row
import service

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "config.ini"

# --------------------
# 設定ファイル
# --------------------

# config.iniの取得
def load_config():
  config = configparser.ConfigParser()
  config.read(CONFIG_FILE, encoding="utf-8")
  return config

# item_config.jsonの取得
def load_item(config):
  filename = (
    BASE_DIR / config["PATH"]["config_dir"] / config["FILE"]["items"]
  )

  try:
    with open(filename, encoding="utf-8") as f:
      item_config = json.load(f)

  except FileNotFoundError:
    raise FileNotFoundError(f"JSONファイルがありません: {filename}")

  if not item_config:
    raise ValueError(f"JSONファイルの内容が空です: {filename}")

  return item_config


# --------------------
# Model
# --------------------
def get_prefectures(config):
  sql = """
    SELECT
      prec_no,
      prefecture_name
    FROM locations
    GROUP BY prec_no, prefecture_name
    ORDER BY prec_no;
  """

  with get_connection(config) as conn:
    with conn.cursor(row_factory=dict_row) as cur:
      cur.execute(sql)

      return cur.fetchall()


def get_locations(prec_no, config):
  sql = """
    SELECT
      station_type,
      block_no,
      prec_no,
      name,
      prefecture_name
    FROM locations
    WHERE prec_no = %s
      AND complete = True
    ORDER BY name;
  """

  with get_connection(config) as conn:
    with conn.cursor(row_factory=dict_row) as cur:
      cur.execute(sql, (prec_no, ))

      return cur.fetchall()


def get_location_dates(station_type, block_no, config):
  sql = """
    SELECT
      l.name,
      l.prefecture_name,
      w.observed_date
    FROM locations AS l
    INNER JOIN weather_observations AS w
      ON l.location_id = w.location_id
    WHERE l.station_type = %s
      AND l.block_no = %s
    ORDER BY w.observed_date DESC;
  """

  with get_connection(config) as conn:
    with conn.cursor(row_factory=dict_row) as cur:
      cur.execute(sql, (station_type, block_no))

      return cur.fetchall()


def get_weather_card(station_type, block_no, date_str, config):
  # HTML生成用のitemを取得
  item_config = load_item(config)

  # index(column)名を和名へ変換するための準備
  column_map = dict(config["COLUMN"])

  # 対象日の実測値を取得
  sql = """
    SELECT
      l.location_id,
      l.station_type,
      l.block_no,
      l.name,
      l.name_en,
      l.prefecture_name,
      l.prefecture_name_en,
      l.start_date,
      l.end_date,
      l.complete,
      l.last_observation_update,
      w.observed_date,
      w.avg_temp,
      w.max_temp,
      w.min_temp,
      w.avg_humidity,
      w.sunshine_hours,
      w.avg_wind_speed,
      w.precipitation,
      w.max_snow_depth
    FROM locations AS l
    LEFT JOIN weather_observations AS w
      ON l.location_id = w.location_id
    WHERE l.station_type = %s
      AND l.block_no = %s
      AND w.observed_date = %s;
  """

  observed_date = datetime.strptime(
    date_str,
    "%Y%m%d"
  ).date()

  with get_connection(config) as conn:
    with conn.cursor(row_factory=dict_row) as cur:
      cur.execute(sql, (station_type, block_no, observed_date))
      weather_row = cur.fetchone()
      target_data = pd.DataFrame([weather_row])
      target_data["observed_date"] = pd.to_datetime(target_data["observed_date"])
      target_data["month"] = target_data["observed_date"].dt.month
      target_data["day"] = target_data["observed_date"].dt.day
      target_data.rename(index=column_map, inplace=True)

  # statsに渡す用のlocation_idを取得
  location_id = weather_row["location_id"]

  # 5つの集計取得を共通タスク化
  stats_tasks = [
    ("daily_avg_stats", service.get_daily_avg_stats, (observed_date, )),
    ("month_avg_stats", service.get_month_avg_stats, (observed_date, )),
    ("overall_avg_stats", service.get_overall_avg_stats, ()),
    ("daily_max_stats", service.get_daily_max_stats, (location_id, observed_date)),
    ("daily_min_stats", service.get_daily_min_stats, (location_id, observed_date))
  ]

  # 集計結果取得
  stats_data = {}
  for name, getter, params in stats_tasks:
    stats_data[name] = pd.DataFrame(getter(config, name, *params))

  # 日ごとの平均値比較結果を取得
  result_daily = service.daily_diff(stats_data["daily_avg_stats"], target_data)
  result_daily.rename(index=column_map, inplace=True)

  # 月ごとの平均値比較結果を取得
  result_month = service.month_diff(stats_data["month_avg_stats"], target_data)
  result_month.rename(index=column_map, inplace=True)

  # 全期間の平均値比較結果を取得
  result_overall = service.all_diff(stats_data["overall_avg_stats"], target_data)
  result_overall.rename(index=column_map, inplace=True)

  # 指定地点 & 指定日 から計算したスコアを取得
  score = service.make_score(
    stats_data["daily_max_stats"],
    stats_data["daily_min_stats"],
    target_data,
    config
  )
  score.rename(index=column_map, inplace=True)

  # スコアのラベルを設定
  label = service.get_score_calc_columns(config)

  # 日ごとのスコアをそれぞれ格納
  score_daily = service.extract_score(score, label, "daily", config)

  # 月ごとのスコアをそれぞれ格納
  score_month = service.extract_score(score, label, "month", config)

  # 全期間のスコアをそれぞれ格納
  score_overall = service.extract_score(score, label, "overall", config)

  # 「比較対象」カラムの値設定
  comparison_month = str(observed_date.month) + "月で比較"
  comparison_daily = str(observed_date.month) + "月" + str(observed_date.day) + "日で比較"
  comparison_overall = "全期間で比較"

  # Controller渡し用にフォーマットを整える
  output_result_daily = service.make_result(
    result_daily, comparison_daily, weather_row, score_daily
  )
  output_result_month = service.make_result(
    result_month, comparison_month, weather_row, score_month
  )
  output_result_overall = service.make_result(
    result_overall, comparison_overall, weather_row, score_overall
  )

  weather_data = pd.concat([
    output_result_daily,
    output_result_month,
    output_result_overall
  ], ignore_index=True)

  groups = service.make_weather_groups(weather_data, item_config)

  return {
    "location": weather_row,
    "groups": groups
  }
