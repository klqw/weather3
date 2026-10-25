import { useState } from "react"
import ExtremeDetails from "./extreme-details"

function WeatherView({weather, dates, onBack, onSelectDate}) {
  const [activeTab, setActiveTab] = useState("day")

  // activeにするデータ値を取得する
  const activeGroup = weather.groups.find(
    group => group.comparison_key === activeTab
  )

  if (!activeGroup) {
    return null
  }

  const date = weather.location.observed_date.replaceAll("-", "")
  const observedDate = weather.location.observed_date
  const [year, month, day] = observedDate.split("-").map(Number)

  // 日付切り替え時の候補日を先に取得
  const beforeYear = getMoveDate(observedDate, "year", "prev")
  const afterYear = getMoveDate(observedDate, "year", "next")
  const beforeMonth = getMoveDate(observedDate, "month", "prev")
  const afterMonth = getMoveDate(observedDate, "month", "next")
  const beforeDay = getMoveDate(observedDate, "day", "prev")
  const afterDay = getMoveDate(observedDate, "day", "next")

  // 候補日が対象地点の観測日に含まれるかをチェック
  const availableDates = new Set(dates.map(date => date.replaceAll("-", "")))
  const hasBeforeYear = availableDates.has(beforeYear)
  const hasAfterYear = availableDates.has(afterYear)
  const hasBeforeMonth = availableDates.has(beforeMonth)
  const hasAfterMonth = availableDates.has(afterMonth)
  const hasBeforeDay = availableDates.has(beforeDay)
  const hasAfterDay = availableDates.has(afterDay)

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

      <div className="date-navigator">
        <div className="date-nav-row">
          <span className="date-nav-label">年</span>
          <button type="button" disabled={!hasBeforeYear} onClick={() => onSelectDate(getMoveDate(observedDate, "year", "prev"))} aria-label="前年">
            ◀
          </button>
          <span className="date-nav-value">{year}年</span>
          <button type="button" disabled={!hasAfterYear} onClick={() => onSelectDate(getMoveDate(observedDate, "year", "next"))} aria-label="翌年">
            ▶
          </button>
        </div>

        <div className="date-nav-row">
          <span className="date-nav-label">月</span>
          <button type="button" disabled={!hasBeforeMonth} onClick={() => onSelectDate(getMoveDate(observedDate, "month", "prev"))} aria-label="前月">
            ◀
          </button>
          <span className="date-nav-value">{month}月</span>
          <button type="button" disabled={!hasAfterMonth} onClick={() => onSelectDate(getMoveDate(observedDate, "month", "next"))} aria-label="翌月">
            ▶
          </button>
        </div>

        <div className="date-nav-row">
          <span className="date-nav-label">日</span>
          <button type="button" disabled={!hasBeforeDay} onClick={() => onSelectDate(getMoveDate(observedDate, "day", "prev"))} aria-label="前日">
            ◀
          </button>
          <span className="date-nav-value">{day}日</span>
          <button type="button" disabled={!hasAfterDay} onClick={() => onSelectDate(getMoveDate(observedDate, "day", "next"))} aria-label="翌日">
            ▶
          </button>
        </div>
      </div>

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

/**
 * 日付移動のための日付取得
  * dateString: YYYY-MM-dd
  * unit: year / month / day
  * direction: prev / next
*/
function getMoveDate(dateString, unit, direction) {
  const [year, month, day] = dateString.split("-").map(Number)
  const move = direction === "prev" ? -1 : 1
  let targetYear = year
  let targetMonth = month
  let targetDay = day

  // year: ±1, month: そのまま, day: 対象日と末日のより小さな値
  if (unit === "year") {
    targetYear += move
    const lastDay = getLastDayOfMonth(targetYear, targetMonth)
    targetDay = Math.min(day, lastDay)
  }

  // year: 1月 & prev = -1, month: ±1 / 1月 & prev = 12, 12月 & next = 1, day: 対象日と末日のより小さな値
  if (unit === "month") {
    targetMonth += move

    // 1月 & prev
    if (targetMonth === 0) {
      targetYear -= 1
      targetMonth = 12
    }

    // 12月 & next
    if (targetMonth === 13) {
      targetYear += 1
      targetMonth = 1
    }

    // 対象日と対象月の末日のより小さな値を設定
    const lastDay = getLastDayOfMonth(targetYear, targetMonth)
    targetDay = Math.min(day, lastDay)
  }

  // day±1の値から日付を取得して対象年月日に設定
  if (unit === "day") {
    const date = new Date(year, month - 1, day + move)

    targetYear = date.getFullYear()
    targetMonth = date.getMonth() + 1
    targetDay = date.getDate()
  }

  return formatApiDate(targetYear, targetMonth, targetDay)

}

// 対象の年月の末日を取得
function getLastDayOfMonth(year, month) {
  return new Date(year, month, 0).getDate()
}

// APIに渡すdateのフォーマット
function formatApiDate(year, month, day) {
  return (
    String(year) + String(month).padStart(2, "0") + String(day).padStart(2, "0")
  )
}

// Viewに渡すdateのフォーマット
function formatDate(dateString) {
  const [year, month, day] = dateString.split("-")
  return `${Number(year)}年${Number(month)}月${Number(day)}日`
}

export default WeatherView