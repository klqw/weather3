import { useEffect, useLayoutEffect, useState } from "react"
import { createRoot } from "react-dom/client"
import LocationDates from "./location-dates"
import WeatherView from "./weather-view"

function WeatherApp() {
  // 都府県
  const [prefectures, setPrefectures] = useState([])
  const [selectedPrecNo, setSelectedPrecNo] = useState("")
  // 地点
  const [locations, setLocations] = useState([])
  const [selectedLocation, setSelectedLocation] = useState(null)
  // 日付
  const [dates, setDates] = useState([])
  // 日付展開状態
  const [openYears, setOpenYears] = useState({})
  const [openMonths, setOpenMonths] = useState({})
  // 日付選択時のスクロール位置
  const [listScrollY, setListScrollY] = useState(0)
  // スクロール位置復元するかどうか
  const [restoreScroll, setRestoreScroll] = useState(false)
  // 日付選択 -> Wether Cardのローディング画面用
  const [isLoading, setIsLoading] = useState(false)
  // WeatherCard
  const [weather, setWeather] = useState(null)
  // SPA <-> 別タブ切り替え
  const [openNewTab, setOpenNewTab] = useState(false)

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

  // 画面を狭くしたときに別タブモードを強制的に解除する
  useEffect(() => {
    const media = window.matchMedia("(max-width: 500px)")

    function handleChange(event) {
      if (event.matches) {
        setOpenNewTab(false)
      }
    }

    if (media.matches) {
      setOpenNewTab(false)
    }

    media.addEventListener("change", handleChange)

    return () => {
      media.removeEventListener("change", handleChange)
    }
  }, [])

  // 日付選択 <-> Weather Cardのスクロール位置調整
  useLayoutEffect(() => {
    // Weather Cardを表示したとき
    if (weather) {
      window.scrollTo({
        top: 250,
        behavior: "auto"
      })
      return
    }
    // 日付選択に戻るとき
    if (restoreScroll) {
      window.scrollTo({
        top: listScrollY,
        behavior: "auto"
      })
      setRestoreScroll(false)
    }
  }, [weather, restoreScroll, listScrollY])

  function handlePrefectureChange(event) {
    setSelectedPrecNo(event.target.value)
    setSelectedLocation(null)
    setDates([])
    setWeather(null)
    setOpenYears({})
    setOpenMonths({})
  }

  function handleLocationChange(event) {
    const value = event.target.value

    if (!value) {
      setSelectedLocation(null)
      setWeather(null)
      setOpenYears({})
      setOpenMonths({})
      return
    }

    const location = locations.find(
      location =>
        `${location.station_type}-${location.block_no}` === value
    )
    setSelectedLocation(location)
    setWeather(null)
    setOpenYears({})
    setOpenMonths({})
  }

  // 地点日付選択 -> WeatherCardAPI
  function selectDateFromList(date) {
    // 日付選択時のスクロール位置保存
    setListScrollY(window.scrollY)
    loadWeather(date)
  }

  // WeatherCard日付選択 -> WeatherCardAPI
  function loadWeather(date) {
    if (!selectedLocation) {
      return
    }

    // ローディングフラグ
    setIsLoading(true)

    fetch(`/api/weather/${selectedLocation.station_type}/${selectedLocation.block_no}/${date}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      return response.json()
    })
    .then(data => {
      setWeather(data)
    })
    .catch(error => {
      console.error(error)
    })
    .finally(() => {
      setIsLoading(false)
    })
  }

  // 日付選択に戻るを押下したときの処理
  function handleBack() {
    setRestoreScroll(true)
    setWeather(null)
  }

  return (
    <div className="weather-selector">
      <div className="selector-options">
        <label className="new-tab-toggle">
          <span className="toggle-label">
            別タブ表示
          </span>
          <input
            type="checkbox" checked={openNewTab}
            onChange={event => setOpenNewTab(event.target.checked)}
          />
          <span className="toggle-switch"></span>
        </label>
      </div>

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

      {!weather && !isLoading && (
        <>
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
             onSelectDate={selectDateFromList}
             openNewTab={openNewTab}
             openYears={openYears}
             setOpenYears={setOpenYears}
             openMonths={openMonths}
             setOpenMonths={setOpenMonths}
            />
          )}
        </>
      )}

      {isLoading && (
        <div className="weather-loading">
          <div className="spinner"></div>
          <div>気象データを読み込んでいます...</div>
        </div>
      )}

      {weather && !isLoading && (
        <WeatherView
         weather={weather}
         dates={dates}
         onBack={handleBack}
         onSelectDate={loadWeather}
        />
      )}
    </div>
  )
}

const rootElement = document.getElementById("weather-app")

createRoot(rootElement).render(
  <WeatherApp />
)