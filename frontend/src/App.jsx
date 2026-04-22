import { useState, useEffect, useCallback } from 'react'
import './App.css'

const API = ''
const REFRESH_MS = 30_000

function fmt(val, decimals = 2) {
  if (val == null) return '—'
  return Math.abs(val).toFixed(decimals)
}

function PowerCard({ label, icon, value, unit = 'kW', accentColor }) {
  return (
    <div className="power-card" style={{ '--accent-color': accentColor }}>
      <div className="card-icon">{icon}</div>
      <div className="card-label">{label}</div>
      <div className="card-value">
        {fmt(value)}
        <span className="card-unit">{unit}</span>
      </div>
    </div>
  )
}

function FlowRow({ label, value }) {
  const active = value != null && Math.abs(value) > 0.001
  return (
    <div className="flow-row">
      <span className="flow-label">{label}</span>
      <span className={`flow-value ${active ? 'active' : 'zero'}`}>
        {value != null ? `${fmt(value)} kW` : '—'}
      </span>
    </div>
  )
}

function StatRow({ label, value, unit }) {
  return (
    <div className="stat-row">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value != null ? `${fmt(value, 1)} ${unit}` : '—'}</span>
    </div>
  )
}

export default function App() {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)
  const [updatedAt, setUpdatedAt] = useState(null)

  const fetchLatest = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/api/latest`)
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.error ?? `HTTP ${res.status}`)
      }
      setData(await res.json())
      setUpdatedAt(new Date())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchLatest()
    const id = setInterval(fetchLatest, REFRESH_MS)
    return () => clearInterval(id)
  }, [fetchLatest])

  const soc  = data?.state_of_charge_percent
  const spot = data?.spot_price_cents_per_kwh

  // Spot price colour
  const spotColor = spot == null ? 'var(--text)'
    : spot < 0  ? 'var(--positive)'
    : spot > 10 ? 'var(--negative)'
    : 'var(--text)'

  return (
    <div className="app">
      <header className="header">
        <h1>Gridle Energy Monitor</h1>
        <div className="header-meta">
          {updatedAt && (
            <span className="timestamp">
              Updated {updatedAt.toLocaleTimeString()}
            </span>
          )}
          <button className="refresh-btn" onClick={fetchLatest} disabled={loading}>
            {loading ? 'Loading…' : 'Refresh'}
          </button>
        </div>
      </header>

      {error && <div className="banner error">Error: {error}</div>}
      {!error && loading && !data && <div className="banner loading">Fetching data…</div>}

      {data && (
        <>
          <p className="section-title">Power</p>
          <div className="power-grid">
            <PowerCard
              label="Solar"
              icon="☀️"
              value={data.solar_power_kw}
              accentColor="var(--solar)"
            />
            <PowerCard
              label="Grid"
              icon="⚡"
              value={data.grid_power_kw}
              accentColor="var(--grid)"
            />
            <PowerCard
              label="House"
              icon="🏠"
              value={data.house_power_kw}
              accentColor="var(--house)"
            />
            <PowerCard
              label="Battery"
              icon="🔋"
              value={data.battery_power_kw}
              accentColor="var(--battery)"
            />
          </div>

          <div className="lower">
            <div className="flow-card">
              <p className="section-title">Energy Flow</p>
              <FlowRow label="Solar → House"   value={data.solar_to_house_kw} />
              <FlowRow label="Solar → Battery" value={data.solar_to_battery_kw} />
              <FlowRow label="Solar → Grid"    value={data.solar_to_grid_kw} />
              <FlowRow label="Grid → House"    value={data.grid_to_house_kw} />
              <FlowRow label="Grid → Battery"  value={data.grid_to_battery_kw} />
              <FlowRow label="Battery → House" value={data.battery_to_house_kw} />
              <FlowRow label="Battery → Grid"  value={data.battery_to_grid_kw} />
            </div>

            <div className="stats-card">
              <p className="section-title">Status</p>

              {/* Battery SOC with bar */}
              <div className="stat-row" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 6 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                  <span className="stat-label">State of Charge</span>
                  <span className="stat-value">{soc != null ? `${soc.toFixed(1)} %` : '—'}</span>
                </div>
                <div className="soc-bar-wrap">
                  <div className="soc-bar-fill" style={{ width: `${soc ?? 0}%` }} />
                </div>
              </div>

              <div className="stat-row">
                <span className="stat-label">Battery Temp</span>
                <span className="stat-value">
                  {data.battery_temperature_celsius != null
                    ? `${data.battery_temperature_celsius.toFixed(1)} °C`
                    : '—'}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Spot Price</span>
                <span className="stat-value" style={{ color: spotColor }}>
                  {spot != null ? `${spot.toFixed(3)} c/kWh` : '—'}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Solar Array 1</span>
                <span className="stat-value">
                  {data.solar_array_1_power_kw != null ? `${fmt(data.solar_array_1_power_kw)} kW` : '—'}
                </span>
              </div>

              <div className="stat-row">
                <span className="stat-label">Solar Array 2</span>
                <span className="stat-value">
                  {data.solar_array_2_power_kw != null ? `${fmt(data.solar_array_2_power_kw)} kW` : '—'}
                </span>
              </div>
            </div>
          </div>

          <p className="period">
            Period: {data.period_start?.replace('T', ' ').replace('Z', ' UTC')}
            {' → '}
            {data.period_end?.replace('T', ' ').replace('Z', ' UTC')}
          </p>
        </>
      )}
    </div>
  )
}
