import { useState } from "react"
import { createRoot } from "react-dom/client"

function ExtremeDetails({locationId, date, metric, comparison, label, extreme, labelColor, unit, enabled}) {
  const [records, setRecords] = useState([])
  const [open, setOpen] = useState(false)

  function handleClick() {
    if (!enabled) {
      return
    }

    fetch(`/api/extremes/${metric}/${comparison}/${extreme}/${locationId}/${date}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      return response.json()
    })
    .then(data => {
      setRecords(data)
      setOpen(true)
    })
    .catch(error => {
      console.error(error)
    })
  }

  return (
    <>
      {enabled ? (
        <button
          type="button"
          className="extreme-link"
          style={{ color: labelColor }}
          onClick={handleClick}
        >{label}</button>
      ) : (
        <span style={{ color: labelColor }}>{label}</span>
      )}

      {open && (
        <div className="extreme-overlay" onClick={() => setOpen(false)}>
          <div className="extreme-popup" onClick={event => event.stopPropagation()}>
            <h4>{extreme === "max" ? "MAX" : "MIN"}記録</h4>

            {records.length > 0 ? (
              <>
                {records[0].total_count > records.length && (
                  <p className="extreme-note">
                    ※ 同率記録 {records[0].total_count}件 のうち {records.length}件 まで表示しています。
                  </p>
                )}
                <div
                 className="extreme-value"
                 style={{ borderLeftColor: labelColor }}
                >
                  {records[0].value}{unit}
                </div>

                {records.map(record => (
                  <div
                   className="extreme-record"
                   key={`${record.location_id}-${record.observed_date}`}
                  >
                    <div>{record.prefecture_name} - {record.name}</div>
                    <div>{formatDate(record.observed_date)}</div>
                  </div>
                ))}
              </>
            ) : (
              <p>該当する記録はありません。</p>
            )}

            <button type="button" className="extreme-close" onClick={() => setOpen(false)}>閉じる</button>
          </div>
        </div>
      )}
    </>
  )
}

function formatDate(dateString) {
  const [year, month, day] = dateString.split("-")
  return `${Number(year)}年${Number(month)}月${Number(day)}日`
}

const rootElements = document.querySelectorAll(".extreme-details")

rootElements.forEach(rootElement => {
  const locationId = rootElement.dataset.locationId
  const date = rootElement.dataset.date
  const metric = rootElement.dataset.metric
  const comparison = rootElement.dataset.comparison
  const label = rootElement.dataset.label
  const extreme = rootElement.dataset.extreme
  const extremes = rootElement.dataset.extremes.split(",")
  const labelColor = rootElement.dataset.labelColor
  const unit = rootElement.dataset.unit
  const enabled = extremes.includes(extreme)

  createRoot(rootElement).render(
    <ExtremeDetails
     locationId={locationId}
     date={date}
     metric={metric}
     comparison={comparison}
     label={label}
     extreme={extreme}
     labelColor={labelColor}
     unit={unit}
     enabled={enabled}
    />
  )
})

export default ExtremeDetails