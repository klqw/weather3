import configparser
import json
import psycopg
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from db import get_connection
from psycopg.rows import dict_row

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

  # 5つの集計取得を共通タスク化
  stats_tasks = [
    ("daily_avg_stats", get_daily_avg_stats),
    ("month_avg_stats", get_month_avg_stats),
    ("overall_avg_stats", get_overall_avg_stats),
    ("daily_max_stats", get_daily_max_stats),
    ("daily_min_stats", get_daily_min_stats)
  ]

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

  # 集計結果取得
  stats_data = {}
  for name, getter in stats_tasks:
    stats_data[name] = pd.DataFrame(getter(config, name))

  # 日ごとの平均値比較結果を取得
  result_daily = daily_diff(stats_data["daily_avg_stats"], target_data)
  result_daily.rename(index=column_map, inplace=True)

  # 月ごとの平均値比較結果を取得
  result_month = month_diff(stats_data["month_avg_stats"], target_data)
  result_month.rename(index=column_map, inplace=True)

  # 全期間の平均値比較結果を取得
  result_overall = all_diff(stats_data["overall_avg_stats"], target_data)
  result_overall.rename(index=column_map, inplace=True)

  # 指定地点 & 指定日 から計算したスコアを取得
  score = make_score(
    stats_data["daily_max_stats"],
    stats_data["daily_min_stats"],
    target_data,
    config
  )
  score.rename(index=column_map, inplace=True)

  # スコアのラベルを設定
  label = get_score_calc_columns(config)

  # 日ごとのスコアをそれぞれ格納
  score_daily = extract_score(score, label, "daily", config)

  # 月ごとのスコアをそれぞれ格納
  score_month = extract_score(score, label, "month", config)

  # 全期間のスコアをそれぞれ格納
  score_overall = extract_score(score, label, "overall", config)

  # 「比較対象」カラムの値設定
  comparison_month = str(observed_date.month) + "月で比較"
  comparison_daily = str(observed_date.month) + "月" + str(observed_date.day) + "日で比較"
  comparison_overall = "全期間で比較"

  # Controller渡し用にフォーマットを整える
  output_result_daily = make_result(
    result_daily, comparison_daily, weather_row, score_daily
  )
  output_result_month = make_result(
    result_month, comparison_month, weather_row, score_month
  )
  output_result_overall = make_result(
    result_overall, comparison_overall, weather_row, score_overall
  )

  weather_data = pd.concat([
    output_result_daily,
    output_result_month,
    output_result_overall
  ], ignore_index=True)

  groups = []

  for comparison, group in weather_data.groupby("比較対象", sort=False):
    items = []

    for _, row in group.iterrows():
      item = row["項目"]
      location_score = int(row["地点スコア"])
      overall_score = int(row["全体スコア"])

      items.append({
        # HTML表示用(文字列)
        "item": item,
        "actual": format_value(row["実測値"]),
        "location_avg": format_value(row["地点基準値"]),
        "location_diff": format_diff(row["差(地点)"]),
        "overall_avg": format_value(row["全体基準値"]),
        "overall_diff": format_diff(row["差(全体)"]),
        "location_score": location_score,
        "overall_score": overall_score,
        "unit": item_config[item]["unit"],
        # HTML表示用(色)
        "actual_color": score_to_color(location_score, item_config[item]),
        "location_score_color": score_to_color(location_score, item_config[item]),
        "overall_score_color": score_to_color(overall_score, item_config[item]),
        "location_diff_color": diff_to_color(float(row["差(地点)"])),
        "overall_diff_color": diff_to_color(float(row["差(全体)"])),
        # スコアバーのラベル文字設定
        "low_label": item_config[item]["low_label"],
        "high_label": item_config[item]["high_label"],
        # スコアバーのラベル色設定
        "low_label_color": item_config[item]["colors"][0],
        "high_label_color": item_config[item]["colors"][4]
      })

    groups.append({
      "comparison": comparison,
      "weather_items": items
    })

  return {
    "location": weather_row,
    "groups": groups
  }


# --------------------
# データ計算
# --------------------

# 1件以上取得確認
def get_stats(cur, sql, stats_name):
  cur.execute(sql)
  rows = cur.fetchall()

  if not rows:
    raise ValueError(f"{stats_name}の取得結果が0件です")

  return rows

# daily_avg_stats取得
def get_daily_avg_stats(config, stats_name):
  sql = """
    SELECT
      location_id,
      month,
      day,
      avg_temp,
      max_temp,
      min_temp,
      avg_humidity,
      sunshine_hours,
      precipitation,
      avg_wind_speed,
      max_snow_depth
    FROM daily_avg_stats;
  """

  try:
    with get_connection(config) as conn:
      with conn.cursor(row_factory=dict_row) as cur:
        return get_stats(cur, sql, stats_name)

  except psycopg.Error as e:
    raise RuntimeError(f"{stats_name}テーブルからの取得に失敗しました") from e

# month_avg_stats取得
def get_month_avg_stats(config, stats_name):
  sql = """
    SELECT
      location_id,
      month,
      avg_temp,
      max_temp,
      min_temp,
      avg_humidity,
      sunshine_hours,
      precipitation,
      avg_wind_speed,
      max_snow_depth
    FROM month_avg_stats;
  """

  try:
    with get_connection(config) as conn:
      with conn.cursor(row_factory=dict_row) as cur:
        return get_stats(cur, sql, stats_name)

  except psycopg.Error as e:
    raise RuntimeError(f"{stats_name}テーブルからの取得に失敗しました") from e

# overall_avg_stats取得
def get_overall_avg_stats(config, stats_name):
  sql = """
    SELECT
      location_id,
      avg_temp,
      max_temp,
      min_temp,
      avg_humidity,
      sunshine_hours,
      precipitation,
      avg_wind_speed,
      max_snow_depth
    FROM overall_avg_stats;
  """

  try:
    with get_connection(config) as conn:
      with conn.cursor(row_factory=dict_row) as cur:
        return get_stats(cur, sql, stats_name)

  except psycopg.Error as e:
    raise RuntimeError(f"{stats_name}テーブルからの取得に失敗しました") from e

# daily_max_stats取得
def get_daily_max_stats(config, stats_name):
  sql = """
    SELECT
      location_id,
      month,
      day,
      avg_temp,
      max_temp,
      min_temp,
      avg_humidity,
      sunshine_hours,
      precipitation,
      avg_wind_speed,
      max_snow_depth
    FROM daily_max_stats;
  """

  try:
    with get_connection(config) as conn:
      with conn.cursor(row_factory=dict_row) as cur:
        return get_stats(cur, sql, stats_name)

  except psycopg.Error as e:
    raise RuntimeError(f"{stats_name}テーブルからの取得に失敗しました") from e

# daily_min_stats取得
def get_daily_min_stats(config, stats_name):
  sql = """
    SELECT
      location_id,
      month,
      day,
      avg_temp,
      max_temp,
      min_temp,
      avg_humidity,
      sunshine_hours,
      precipitation,
      avg_wind_speed,
      max_snow_depth
    FROM daily_min_stats;
  """

  try:
    with get_connection(config) as conn:
      with conn.cursor(row_factory=dict_row) as cur:
        return get_stats(cur, sql, stats_name)

  except psycopg.Error as e:
    raise RuntimeError(f"{stats_name}テーブルからの取得に失敗しました") from e

# 表示項目の設定
def get_temp_columns():
  return [
    "avg_temp",        # 平均気温(℃)
    "max_temp",        # 最高気温(℃)
    "min_temp",        # 最低気温(℃)
    "avg_humidity",    # 平均湿度(％)
    "sunshine_hours",  # 日照時間(時間)
    "avg_wind_speed",  # 平均風速(m/s)
    "precipitation",   # 降水量の合計(mm)
    "max_snow_depth"   # 最深積雪(cm)
  ]

# 差分の計算(NaN値対策)
def calc_diff(actual, base):
  result = actual.copy()

  for column in actual.index:
    if pd.isna(actual[column]) or pd.isna(base[column]):
      result[column] = np.nan

    else:
      result[column] = actual[column] - base[column]

  return result

# スコアの計算(NaN値対策)
def calc_score(base_value, max_value, min_value):
  result = base_value.copy()

  for column in base_value.index:
    if pd.isna(base_value[column]) or pd.isna(max_value[column]) or pd.isna(min_value[column]):
      result[column] = 0

    elif max_value[column] == min_value[column]:
      result[column] = 0

    else:
      result[column] = (base_value[column] - min_value[column]) / (max_value[column] - min_value[column]) * 99 + 1

  return result

# スコア計算時のラベル(カラム名)を設定
def get_score_calc_columns(config):
  return {
    "loc_day": config["SCORE_LABEL"]["location_daily_score"],
    "loc_mon": config["SCORE_LABEL"]["location_month_score"],
    "loc_all": config["SCORE_LABEL"]["location_overall_score"],
    "all_day": config["SCORE_LABEL"]["all_daily_score"],
    "all_mon": config["SCORE_LABEL"]["all_month_score"],
    "all_all": config["SCORE_LABEL"]["all_overall_score"]
  }

# スコア出力時のラベル(カラム名)を設定
def get_score_out_columns(config):
  return [
    config["SCORE_LABEL"]["output_location_score"],
    config["SCORE_LABEL"]["output_all_score"]
  ]

# 日ごと、月ごと、全期間に合わせてスコアを格納
def extract_score(score, label, period, config):
  columns = {
    "daily": [label["loc_day"], label["all_day"]],  # 日ごと
    "month": [label["loc_mon"], label["all_mon"]],  # 月ごと
    "overall": [label["loc_all"], label["all_all"]] # 全期間
  }

  if period not in columns:
    raise ValueError(f"不正な期間です: {period}")

  result = score[columns[period]].copy()
  result.columns = get_score_out_columns(config)
  # print(result)

  return result


# 指定日の実測値を取得
def get_target_temp(df, target_date):
  return df[
    df["observed_date"] == target_date
  ]

# --------------------
# 指定日付の差分分析
# --------------------

# 指定日と日ごとの比較
def daily_diff(df, target_data):

  # ターゲット地点のlocation_idを取得
  location_id = target_data["location_id"].iloc[0]

  # 指定日の月・日を取得
  target_month = target_data["month"].iloc[0]
  target_day = target_data["day"].iloc[0]

  # 指定日の月・日に対する平均値を取得
  df = df[
    (df["month"] == target_month) &
    (df["day"] == target_day)
  ]

  # 全地点の指定日の月・日に対する平均値を取得
  all_avg = df.groupby(["location_id", "month", "day"])[
    get_temp_columns()
  ].mean()
  all_avg = all_avg.mean().to_frame().T
  # print(all_avg)

  # ターゲット地点の指定日の月・日に対する平均値を取得
  target_avg = df[
    df["location_id"] == location_id
  ]
  # print(target_avg)

  # target_tempを比較用に加工
  actual = target_data[
    get_temp_columns()
  ].iloc[0]

  # 全地点の指定日の月・日に対する平均値を比較用に加工
  base_all = all_avg[
    get_temp_columns()
  ].iloc[0]

  # ターゲット地点の指定日の月・日に対する平均値を比較ように加工
  base_target = target_avg[
    get_temp_columns()
  ].iloc[0]

  return pd.DataFrame({
    "実測値": actual,
    "地点基準値": base_target,
    "差(地点)": calc_diff(actual, base_target),
    "全体基準値": base_all,
    "差(全体)": calc_diff(actual, base_all)
  }).round(1)

# 指定日と月ごとの比較
def month_diff(df, target_data):

  # ターゲット地点のlocation_idを取得
  location_id = target_data["location_id"].iloc[0]

  # 指定日の月を取得
  target_month = target_data["month"].iloc[0]

  # 指定日の月に対応する平均値を取得
  df = df[
    df["month"] == target_month
  ]

  # 全地点の指定日の月に対する平均値を取得
  all_avg = df.groupby(["location_id", "month"])[
    get_temp_columns()
  ].mean()
  all_avg = all_avg.mean().to_frame().T
  # print(all_avg)

  # ターゲット地点の指定日の月に対する平均値を取得
  target_avg = df[
    df["location_id"] == location_id
  ]
  # print(target_avg)

  # target_dataを比較用に加工
  actual = target_data[
    get_temp_columns()
  ].iloc[0]

  # 全地点の指定日の月に対する平均値を比較用に加工
  base_all = all_avg[
    get_temp_columns()
  ].iloc[0]

  # ターゲット地点の指定日の月に対する平均値を比較用に加工
  base_target = target_avg[
    get_temp_columns()
  ].iloc[0]

  return pd.DataFrame({
    "実測値": actual,
    "地点基準値": base_target,
    "差(地点)": calc_diff(actual, base_target),
    "全体基準値": base_all,
    "差(全体)": calc_diff(actual, base_all)
  }).round(1)

# 指定日と全期間の比較
def all_diff(df, target_data):

  # ターゲット地点のlocation_idを取得
  location_id = target_data["location_id"].iloc[0]

  # 全地点の平均値を取得
  all_avg = df.mean(numeric_only=True).to_frame().T
  # print(all_avg)

  # ターゲット地点の平均値を取得
  target_avg = df[
    df["location_id"] == location_id
  ]
  # print(target_avg)

  # target_tempを比較用に加工
  actual = target_data[
    get_temp_columns()
  ].iloc[0]

  # 全地点の平均値を比較用に加工
  base_all = all_avg[
    get_temp_columns()
  ].iloc[0]

  # ターゲット地点の平均値を比較用に加工
  base_target = target_avg[
    get_temp_columns()
  ].iloc[0]

  return pd.DataFrame({
    "実測値": actual,
    "地点基準値": base_target,
    "差(地点)": calc_diff(actual ,base_target),
    "全体基準値": base_all,
    "差(全体)": calc_diff(actual, base_all)
  }).round(1)
  
# 指定日の最大値と最小値からスコア計算したdfを出力
def make_score(max_df, min_df, target_data, config):

  # ターゲット地点のlocation_idを取得
  location_id = target_data["location_id"].iloc[0]

  # 指定日の月・日を取得
  target_month = target_data["month"].iloc[0]
  target_day = target_data["day"].iloc[0]

  # 指定地点 & 指定日の最大値を取得
  max_location_daily_df = max_df[
    (max_df["location_id"] == location_id) &
    (max_df["month"] == target_month) &
    (max_df["day"] == target_day)
  ]
  # スコア計算用に加工
  max_loc_day = max_location_daily_df[
    get_temp_columns()
  ].iloc[0]

  # 指定地点 & 指定月の最大値を取得
  max_location_month_df = max_df[
    (max_df["location_id"] == location_id) &
    (max_df["month"] == target_month)
  ]
  # スコア計算用に加工
  max_loc_mon = max_location_month_df[
    get_temp_columns()
  ].max()

  # 指定地点 & 全期間の最大値を取得
  max_location_all_df = max_df[
    (max_df["location_id"] == location_id)
  ]
  # スコア計算用に加工
  max_loc_all = max_location_all_df[
    get_temp_columns()
  ].max()

  # 全地点 指定日の最大値を取得
  max_daily_df = max_df[
    (max_df["month"] == target_month) &
    (max_df["day"] == target_day)
  ]
  # スコア計算用に加工
  max_day = max_daily_df[
    get_temp_columns()
  ].max()

  # 全地点 & 指定月の最大値を取得
  max_month_df = max_df[
    (max_df["month"] == target_month)
  ]
  # スコア計算用に加工
  max_mon = max_month_df[
    get_temp_columns()
  ].max()

  # 全地点 & 全期間の最大値を取得、加工
  max_all = max_df[
    get_temp_columns()
  ].max()

  # 指定地点 & 指定日の最小値を取得
  min_location_daily_df = min_df[
    (min_df["location_id"] == location_id) &
    (min_df["month"] == target_month) &
    (min_df["day"] == target_day)
  ]
  # スコア計算用に加工
  min_loc_day = min_location_daily_df[
    get_temp_columns()
  ].iloc[0]

  # 指定地点 & 指定月の最小値を取得
  min_location_month_df = min_df[
    (min_df["location_id"] == location_id) &
    (min_df["month"] == target_month)
  ]
  # スコア計算用に加工
  min_loc_mon = min_location_month_df[
    get_temp_columns()
  ].min()

  # 指定地点 & 全期間の最小値を取得
  min_location_all_df = min_df[
    (min_df["location_id"] == location_id)
  ]
  # スコア計算用に加工
  min_loc_all = min_location_all_df[
    get_temp_columns()
  ].min()

  # 全地点 指定日の最小値を取得
  min_daily_df = min_df[
    (min_df["month"] == target_month) &
    (min_df["day"] == target_day)
  ]
  # スコア計算用に加工
  min_day = min_daily_df[
    get_temp_columns()
  ].min()

  # 全地点 & 指定月の最小値を取得
  min_month_df = min_df[
    (min_df["month"] == target_month)
  ]
  # スコア計算用に加工
  min_mon = min_month_df[
    get_temp_columns()
  ].min()

  # 全地点 & 全期間の最小値を取得、加工
  min_all = min_df[
    get_temp_columns()
  ].min()

  """
  print("指定地点・指定日")
  print(max_loc_day)
  print(min_loc_day)
  print("指定地点・指定月")
  print(max_loc_mon)
  print(min_loc_mon)
  print("指定地点・全期間")
  print(max_loc_all)
  print(min_loc_all)
  print("全地点・指定日")
  print(max_day)
  print(min_day)
  print("全地点・指定月")
  print(max_mon)
  print(min_mon)
  print("全地点・全期間")
  print(max_all)
  print(min_all)
  """
  
  # 基準値の整形
  base = target_data[
    get_temp_columns()
  ].iloc[0]

  # スコアのラベル(カラム名)を設定
  label = get_score_calc_columns(config)

  # スコア計算
  result = pd.DataFrame({
    label["loc_day"]: calc_score(base, max_loc_day, min_loc_day),
    label["loc_mon"]: calc_score(base, max_loc_mon, min_loc_mon),
    label["loc_all"]: calc_score(base, max_loc_all, min_loc_all),
    label["all_day"]: calc_score(base, max_day, min_day),
    label["all_mon"]: calc_score(base, max_mon, min_mon),
    label["all_all"]: calc_score(base, max_all, min_all)
  }).round().astype(int)

  return result


# --------------------
# 計算結果整形
# --------------------
def make_result(result, comparison, location_data, score):

  # 出力用DataFrameに 比較対象, 地点, スコアを追加
  result = result.copy()
  result.insert(0, "比較対象", comparison)
  result.insert(1, "地点", location_data["name"])
  result.insert(2, "都府県", location_data["prefecture_name"])
  result = result.reset_index()
  result = result.rename(columns={"index": "項目"})
  result = result.join(
    score,
    on="項目"
  )

  return result


# --------------------
# HTML出力用のデータ整形
# --------------------

# NaN値の場合、「－」に置換
def format_value(value):
  return "－" if pd.isna(value) else value

def format_diff(value):
  if pd.isna(value):
    return "－"
  return f"{value:+.1f}"

# 色変換 HEX -> RGB
def hex_to_rgb(hex_color):
  r = int(hex_color[1:3], 16)
  g = int(hex_color[3:5], 16)
  b = int(hex_color[5:7], 16)

  return r, g, b

# スコアによってバッジの表示/非表示を設定
def make_score_marker(score, color):
  if score == 0:
    return ""

  return f"""
    <span class="marker"
      style="left: {score}%; background-color: {color};">
      {score}
    </span>
  """

# スコアごとにマーカーとバッジの背景色設定
def score_to_color(score, item_config):
  """
  スコア 1～100を
  青 → 水色 → 緑 → オレンジ → 赤
  のようにグラデーションに変換する
  """
  # 色の基準設定(HEX)
  colors = item_config["colors"]
  # RGBに変換
  colors = [hex_to_rgb(color) for color in colors]

  # スコア 1～100 → 0～4 に変換
  score = max(1, min(100, score))
  position = (score - 1) / 99 * 4
  index = int(position)

  # 100点の場合
  if index >= 4:
    r, g, b = colors[4]
    return f"rgb({r}, {g}, {b})"

  # グラデーション設定
  ratio = position - index
  r1, g1, b1 = colors[index]
  r2, g2, b2 = colors[index + 1]

  # RGB値計算
  r = round(r1 + (r2 - r1) * ratio)
  g = round(g1 + (g2 - g1) * ratio)
  b = round(b1 + (b2 - b1) * ratio)

  return f"rgb({r}, {g}, {b})"

# 差分の文字色設定
def diff_to_color(diff):
  if diff > 0.0:
    color = "positive"
  elif diff < 0.0:
    color = "negative"
  else:
    color = "zero"

  return color
