import { useState } from "react"
import { createRoot } from "react-dom/client"

function ExtremeDetails({locationId, date, metric, comparison, label, extreme, labelColor, enabled}) {
  // const [records, setRecords] = useState([])
  // const [open, setOpen] = useState(false)

  function handleClick() {
    if (!enabled) {
      return
    }

    fetch(`/api/extremes/${metric}/${comparison}/${extreme}/${locationId}/${date}`)
    .then(response => response.json())
    .then(data => {
      // setRecords(data)
      // setOpen(true)
      console.log(data)
    })
  }

  if (!enabled) {
    return (
      <span style={{ color: labelColor }}>{label}</span>
    )
  }

  return (
    <button
      type="button"
      className="extreme-link"
      style={{ color: labelColor }}
      onClick={handleClick}
    >{label}</button>

    // {open && (
    //   <div>
    //     {records.map(record => (
    //       <div key={`${record.extreme_type}-${record.observed_date}`}>
    //         {record.extreme_type}
    //         {record.value}
    //         {record.observed_date}
    //       </div>
    //     ))}
    //     <button onClick={() => setOpen(false)}>閉じる</button>
    //   </div>
    // )}
  )
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
     enabled={enabled}
    />
  )
})
