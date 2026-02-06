// src/pages/EvidencePage.tsx
import React, { useState, useEffect } from 'react'
import { apiClient, Evidence, Target } from '../services/apiClient'

export default function EvidencePage() {
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [targets, setTargets] = useState<Target[]>([])
  const [loading, setLoading] = useState(true)
  const [showCaptureModal, setShowCaptureModal] = useState(false)
  const [captureForm, setCaptureForm] = useState({
    url: '',
    target_id: '',
    finding_id: '',
    capture_types: ['fullpage', 'http'],
  })
  const [capturing, setCapturing] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [evidenceData, targetsData] = await Promise.all([
        apiClient.getEvidence(),
        apiClient.getTargets(),
      ])
      setEvidence(evidenceData)
      setTargets(targetsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getTargetName = (targetId: number) => {
    const target = targets.find(t => t.id === targetId)
    return target?.name || `Target ${targetId}`
  }

  const handleCapture = async (e: React.FormEvent) => {
    e.preventDefault()
    setCapturing(true)
    try {
      const result = await apiClient.captureEvidence({
        url: captureForm.url,
        target_id: parseInt(captureForm.target_id),
        finding_id: captureForm.finding_id ? parseInt(captureForm.finding_id) : undefined,
        capture_types: captureForm.capture_types,
      })
      
      if (result.success) {
        alert(`Evidence captured! ${result.captured} items captured, ${result.failed} failed.`)
        setShowCaptureModal(false)
        loadData()
      } else {
        alert('Evidence capture failed. Check console for details.')
      }
    } catch (error: any) {
      alert(`Capture failed: ${error.message}`)
    } finally {
      setCapturing(false)
    }
  }

  const handleToggleCaptureType = (type: string) => {
    const types = captureForm.capture_types
    if (types.includes(type)) {
      setCaptureForm({ ...captureForm, capture_types: types.filter(t => t !== type) })
    } else {
      setCaptureForm({ ...captureForm, capture_types: [...types, type] })
    }
  }

  const getEvidenceIcon = (type: string) => {
    const icons: Record<string, string> = {
      screenshot_fullpage: '🖼️',
      screenshot_mobile: '📱',
      screenshot_element: '🎯',
      http_response: '🌐',
      network_log: '📊',
    }
    return icons[type] || '📄'
  }

  if (loading) {
    return <div className="text-center py-12">Loading evidence...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Evidence</h1>
        <button
          onClick={() => setShowCaptureModal(true)}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          + Capture Evidence
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {evidence.map((item) => (
          <div key={item.id} className="bg-white rounded-lg shadow p-4 border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="text-3xl">{getEvidenceIcon(item.type)}</div>
              <span className="text-xs text-gray-500">
                {new Date(item.created_at).toLocaleDateString()}
              </span>
            </div>
            
            <h3 className="text-sm font-semibold text-gray-900 mb-2">{item.type.replace(/_/g, ' ').toUpperCase()}</h3>
            
            <div className="text-xs text-gray-600 space-y-1 mb-3">
              <div>Target: {getTargetName(item.target_id)}</div>
              {item.finding_id && <div>Finding: #{item.finding_id}</div>}
              {item.meta?.url && (
                <div className="truncate">URL: {item.meta.url}</div>
              )}
            </div>

            {item.file_path && item.type.includes('screenshot') && (
              <div className="mb-3">
                <img
                  src={`http://localhost:8000/${item.file_path}`}
                  alt={item.type}
                  className="w-full h-32 object-cover rounded border border-gray-200"
                />
              </div>
            )}

            {item.file_path && (
              <a
                href={`http://localhost:8000/${item.file_path}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700 transition-colors"
              >
                View Full
              </a>
            )}
          </div>
        ))}
      </div>

      {evidence.length === 0 && (
        <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
          No evidence captured yet. Start capturing screenshots and HTTP responses!
        </div>
      )}

      {showCaptureModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Capture Evidence</h2>
            <form onSubmit={handleCapture} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target URL</label>
                <input
                  type="url"
                  value={captureForm.url}
                  onChange={(e) => setCaptureForm({ ...captureForm, url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  required
                  placeholder="https://example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Target</label>
                <select
                  value={captureForm.target_id}
                  onChange={(e) => setCaptureForm({ ...captureForm, target_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  required
                >
                  <option value="">Select a target</option>
                  {targets.map(target => (
                    <option key={target.id} value={target.id}>{target.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Capture Types</label>
                <div className="space-y-2">
                  {['fullpage', 'mobile', 'http', 'network'].map(type => (
                    <label key={type} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={captureForm.capture_types.includes(type)}
                        onChange={() => handleToggleCaptureType(type)}
                        className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                      />
                      <span className="ml-2 text-sm text-gray-700">{type.charAt(0).toUpperCase() + type.slice(1)}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  disabled={capturing}
                  className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:bg-gray-400"
                >
                  {capturing ? 'Capturing...' : 'Capture'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCaptureModal(false)}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

// src/pages/SchedulerPage.tsx
import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/apiClient'

export default function SchedulerPage() {
  const [status, setStatus] = useState({ enabled: false, interval_hours: 24 })
  const [running, setRunning] = useState(false)
  const [lastResult, setLastResult] = useState<any>(null)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      const data = await fetch('http://localhost:8000/api/scheduler/status').then(r => r.json())
      setStatus(data)
    } catch (error) {
      console.error('Failed to load scheduler status:', error)
    }
  }

  const handleRunScheduler = async () => {
    setRunning(true)
    try {
      const result = await apiClient.runScheduler()
      setLastResult(result.results)
      alert(`Scheduler completed! ${result.results.new_findings} new findings discovered.`)
    } catch (error: any) {
      alert(`Scheduler failed: ${error.message}`)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Scheduler</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Scheduler Status</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Status:</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              status.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {status.enabled ? 'Enabled' : 'Disabled'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Interval:</span>
            <span className="text-gray-900 font-medium">{status.interval_hours} hours</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Manual Execution</h2>
        <p className="text-gray-600 mb-4">
          Run the scheduler manually to scan all enabled targets for new vulnerabilities.
        </p>
        <button
          onClick={handleRunScheduler}
          disabled={running}
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {running ? 'Running...' : 'Run Scheduler Now'}
        </button>
      </div>

      {lastResult && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Last Run Results</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Total Targets:</span>
              <span className="text-gray-900 font-medium">{lastResult.total_targets}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Successful:</span>
              <span className="text-green-600 font-medium">{lastResult.successful}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Failed:</span>
              <span className="text-red-600 font-medium">{lastResult.failed}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">New Findings:</span>
              <span className="text-blue-600 font-medium">{lastResult.new_findings}</span>
            </div>
          </div>

          {lastResult.targets_processed && lastResult.targets_processed.length > 0 && (
            <div className="mt-4">
              <h3 className="font-medium text-gray-900 mb-2">Processed Targets:</h3>
              <div className="space-y-2">
                {lastResult.targets_processed.map((target: any) => (
                  <div key={target.target_id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span className="text-sm text-gray-700">{target.target_name}</span>
                    <span className="text-sm text-gray-500">{target.new_findings} new</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// src/pages/SettingsPage.tsx
import React, { useState, useEffect } from 'react'
import { apiClient } from '../services/apiClient'

export default function SettingsPage() {
  const [config, setConfig] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const data = await apiClient.getConfig()
      setConfig(data)
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading settings...</div>
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Settings</h1>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">HackerOne Configuration</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">API Token:</span>
            <span className={`px-3 py-1 rounded text-sm ${
              config?.hackerone?.token_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {config?.hackerone?.token_configured ? `Configured (${config.hackerone.token_masked})` : 'Not Configured'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Team Handle:</span>
            <span className="text-gray-900">{config?.hackerone?.team_handle || 'Not Set'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">API URL:</span>
            <span className="text-gray-900 text-sm">{config?.hackerone?.api_url}</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Telegram Configuration</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Bot Token:</span>
            <span className={`px-3 py-1 rounded text-sm ${
              config?.telegram?.bot_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {config?.telegram?.bot_configured ? 'Configured' : 'Not Configured'}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Chat ID:</span>
            <span className="text-gray-900">{config?.telegram?.chat_id || 'Not Set'}</span>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Slack Configuration</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Webhook:</span>
            <span className={`px-3 py-1 rounded text-sm ${
              config?.slack?.webhook_configured ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            }`}>
              {config?.slack?.webhook_configured ? 'Configured' : 'Not Configured'}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-blue-900 mb-2">⚙️ Configuration Instructions</h3>
        <p className="text-sm text-blue-800">
          To configure API keys and settings, edit the <code className="bg-blue-100 px-2 py-1 rounded">.env</code> file 
          in the backend directory and restart the server.
        </p>
      </div>
    </div>
  )
}