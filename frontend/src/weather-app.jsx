import { useEffect, useState } from "react"
import { createRoot } from "react-dom/client"
import LocationDates from "./location-dates"

function WeatherApp() {
  // 都府県
  const [prefectures, setPrefectures] = useState([])
  const [selectedPrecNo, setSelectedPrecNo] = useState("")
  // 地点
  const [locations, setLocations] = useState([])
  const [selectedLocation, setSelectedLocation] = useState(null)
  // 日付
  const [dates, setDates] = useState([])

  // ページを読み込んだら都府県APIを呼ぶ
  useEffect(() => {
    fetch("/api/prefectures")
    .then(response => response.json())
    .then(data => {
      setPrefectures(data)
    })
  }, [])

  // 都府県を選択したら地点APIを呼ぶ
  useEffect(() => {
    if (!selectedPrecNo) {
      setLocations([])
      return
    }

    fetch(`/api/locations/${selectedPrecNo}`)
    .then(response => response.json())
    .then(data => {
      setLocations(data)
    })
  }, [selectedPrecNo])

  // 地点を選択したら日付APIを呼ぶ
  useEffect(() => {
    if (!selectedLocation) {
      setDates([])
      return
    }

    fetch(`/api/location/${selectedLocation.station_type}/${selectedLocation.block_no}/dates`)
    .then(response => response.json())
    .then(data => {
      setDates(data)
    })
  }, [selectedLocation])

  function handlePrefectureChange(event) {
    setSelectedPrecNo(event.target.value)
    setSelectedLocation(null)
  }

  function handleLocationChange(event) {
    const value = event.target.value

    if (!value) {
      setSelectedLocation(null)
      return
    }

    const location = locations.find(
      location =>
        `${location.station_type}-${location.block_no}` === value
    )
    setSelectedLocation(location)
  }

  return (
    <div className="weather-selector">
      <div className="select-group">
        <label htmlFor="prefecture-select">
          都府県
        </label>

        <select id="prefecture-select" value={selectedPrecNo} onChange={handlePrefectureChange}>
          <option value="">
            都府県を選択してください
          </option>

          {prefectures.map(prefecture => (
            <option key={prefecture.prec_no} value={prefecture.prec_no}>
              {prefecture.prefecture_name}
            </option>
          ))}
        </select>
      </div>

      <div className="select-group">
        <label htmlFor="location-select">
          地点
        </label>

        <select id="location-select" onChange={handleLocationChange} disabled={locations.length === 0}>
          <option value="">
            地点を選択してください
          </option>
          
          {locations.map(location => (
            <option
             key={`${location.station_type}-${location.block_no}`}
             value={`${location.station_type}-${location.block_no}`}
            >
              {location.name}
            </option>
          ))}
        </select>
      </div>

      {selectedLocation && (
        <div className="selected-location">
          {selectedLocation.prefecture_name}
          <strong>{selectedLocation.name}</strong>
        </div>
      )}

      {selectedLocation && dates.length > 0 && (
        <LocationDates
         dates={dates}
         stationType={selectedLocation.station_type}
         blockNo={selectedLocation.block_no}
        />
      )}
    </div>
  )
}

const rootElement = document.getElementById("weather-app")

createRoot(rootElement).render(
  <WeatherApp />
)