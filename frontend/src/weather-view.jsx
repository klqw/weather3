import { useState } from "react"
import ExtremeDetails from "./extreme-details"

function WeatherView({weather, onBack}) {
  const [activeTab, setActiveTab] = useState("day")

  // activeにするデータ値を取得する
  const activeGroup = weather.groups.find(
    group => group.comparison_key === activeTab
  )

  if (!activeGroup) {
    return null
  }

  const date = weather.location.observed_date.replaceAll("-", "")

  return (
    <div className="weather-view">
      <header className="header">
        <h1>
          {formatDate(weather.location.observed_date)}
          {" "}
          {weather.location.name}
          {" - "}
          {weather.location.prefecture_name}
        </h1>
      </header>

      <button type="button" className="weather-back" onClick={onBack}>←日付選択に戻る</button>

      <div className="weather-tabs">
        <button
          type="button"
          className={activeTab === "day" ? "active" : ""}
          onClick={() => setActiveTab("day")}
        >
          Daily
        </button>
        <button
          type="button"
          className={activeTab === "mon" ? "active" : ""}
          onClick={() => setActiveTab("mon")}
        >
          Month
        </button>
        <button
          type="button"
          className={activeTab === "all" ? "active" : ""}
          onClick={() => setActiveTab("all")}>
          Overall
        </button>
      </div>

      <div className="weather-card">
        <h2>{activeGroup.comparison}</h2>

        {activeGroup.weather_items.map((item, index) => (
          <div key={item.metric}>
            <h3>{item.item}</h3>
            <div className="actual">
              実測値 <strong style={{color: item.actual_color}}>
                {item.actual}{item.unit}
              </strong>
            </div>
          <div className="averages">
            <span>地点平均 {item.location_avg}{item.unit}</span>
            <span>全体平均 {item.overall_avg}{item.unit}</span>
          </div>

          <div className="differences">
            <span>地点平均との差{" "}
              <span className={item.location_diff_color}>
                {item.location_diff}{item.unit}
              </span>
            </span>
            <span>全体平均との差{" "}
              <span className={item.overall_diff_color}>
                {item.overall_diff}{item.unit}
              </span>
            </span>
          </div>

          <div className="score-group">
            <div className="score-row">
              <span className="score-label">地点</span>
              <div className="extreme-details low">
                <ExtremeDetails
                  locationId={weather.location.location_id}
                  date={date}
                  metric={item.metric}
                  comparison={`loc_${activeGroup.comparison_key}`}
                  label={item.low_label}
                  extreme="min"
                  labelColor={item.low_label_color}
                  unit={item.unit}
                  enabled={item.extremes.includes("min")}
                />
              </div>


              <div className="bar">
                <div
                  className="bar-fill"
                  style={{
                    width: `${item.location_score}%`,
                    backgroundColor: item.location_score_color
                  }}
                />
                {item.location_score !== 0 && (
                  <span
                    className="marker"
                    style={{
                      left: `${item.location_score}%`,
                      backgroundColor: item.location_score_color
                    }}
                  >
                    {item.location_score}
                  </span>
                )}
              </div>

              <div className="extreme high">
                <ExtremeDetails
                 locationId={weather.location.location_id}
                 date={date}
                 metric={item.metric}
                 comparison={`loc_${activeGroup.comparison_key}`}
                 label={item.high_label}
                 extreme="max"
                 labelColor={item.high_label_color}
                 unit={item.unit}
                 enabled={item.extremes.includes("max")}
                />
              </div>

            </div>

            <div className="score-row">
              <span className="score-label">全体</span>
              <div className="extreme-details low">
                <ExtremeDetails
                  locationId={weather.location.location_id}
                  date={date}
                  metric={item.metric}
                  comparison={`all_${activeGroup.comparison_key}`}
                  label={item.low_label}
                  extreme="min"
                  labelColor={item.low_label_color}
                  unit={item.unit}
                  enabled={item.extremes.includes("min")}
                />
              </div>

              <div className="bar">
                <div
                  className="bar-fill"
                  style={{
                    width: `${item.overall_score}%`,
                    backgroundColor: item.overall_score_color
                  }}
                />
                {item.overall_score !== 0 && (
                  <span
                    className="marker"
                    style={{
                      left: `${item.overall_score}%`,
                      backgroundColor: item.overall_score_color
                    }}
                  >
                    {item.overall_score}
                  </span>
                )}
              </div>

              <div className="extreme-details high">
                <ExtremeDetails
                 locationId={weather.location.location_id}
                 date={date}
                 metric={item.metric}
                 comparison={`all_${activeGroup.comparison_key}`}
                 label={item.high_label}
                 extreme="max"
                 labelColor={item.high_label_color}
                 unit={item.unit}
                 enabled={item.extremes.includes("max")}
                />
              </div>

            </div>
          </div>

          {index !== activeGroup.weather_items.length - 1 && (
            <hr />
          )}
          </div>
        ))}
      </div>
    </div>
  )
}

function formatDate(dateString) {
  const [year, month, day] = dateString.split("-")
  return `${Number(year)}年${Number(month)}月${Number(day)}日`
}

export default WeatherView