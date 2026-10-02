import { useState } from "react"
import { createRoot } from "react-dom/client"

function groupDates(dates) {
  const grouped = {}

  for (const date of dates) {
    const [year, month, day] = date.split("-").map(Number)

    if (!grouped[year]) {
      grouped[year] = {}
    }

    if (!grouped[year][month]) {
      grouped[year][month] = []
    }

    grouped[year][month].push({
      day,
      date: date.replaceAll("-", "")
    })
  }

  return grouped
}

function LocationDates({
  dates,
  stationType,
  blockNo
}) {
  const grouped = groupDates(dates)

  const [openYears, setOpenYears] = useState({})
  const [openMonths, setOpenMonths] = useState({})

  function toggleYear(year) {
    setOpenYears(prev => ({
      ...prev,
      [year]: !prev[year]
    }))
  }

  function toggleMonth(year, month) {
    const key = `${year}-${month}`

    setOpenMonths(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  return (
    <div className="date-list">
      {Object.entries(grouped)
      .sort(([a], [b]) => Number(b) - Number(a))
      .map(([year, months]) => (
        <div className="date-year" key={year}>
          <button className="date-toggle year-toggle" onClick={() => toggleYear(year)}>
            {openYears[year] ? "▼" : "▶"}
            {year}年
          </button>
          {openYears[year] && (
            <div className="date-months">
              {Object.entries(months)
              .sort(([a], [b]) => Number(b) - Number(a))
              .map(([month, days]) => {
                const key = `${year}-${month}`

                return (
                  <div className="date-month" key={key}>
                    <button className="date-toggle month-toggle" onClick={() => toggleMonth(year, month)}>
                      {openMonths[key] ? "▼" : "▶"}
                      {month}月
                    </button>
                    {openMonths[key] && (
                      <div className="date-days">
                        {days.map(({ day, date }) => (
                          <a key={date} href={`/weather/${stationType}/${blockNo}/${date}`} target="_blank">
                            {day}日
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

const element = document.getElementById("location-dates-data")
const dates = JSON.parse(element.textContent)
const rootElement = document.getElementById("location-dates")
const stationType = rootElement.dataset.stationType
const blockNo = rootElement.dataset.blockNo

createRoot(rootElement).render(
  <LocationDates
  dates={dates}
  stationType={stationType}
  blockNo={blockNo}
  />
)