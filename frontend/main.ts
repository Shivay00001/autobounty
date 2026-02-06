// src/main.tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)

// src/App.tsx
import React, { useState } from 'react'
import Dashboard from './pages/Dashboard'
import TargetsPage from './pages/TargetsPage'
import FindingsPage from './pages/FindingsPage'
import ReportsPage from './pages/ReportsPage'
import EvidencePage from './pages/EvidencePage'
import SettingsPage from './pages/SettingsPage'
import SchedulerPage from './pages/SchedulerPage'

type Page = 'dashboard' | 'targets' | 'findings' | 'reports' | 'evidence' | 'settings' | 'scheduler'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'targets', label: 'Targets', icon: '🎯' },
    { id: 'findings', label: 'Findings', icon: '🔍' },
    { id: 'reports', label: 'Reports', icon: '📄' },
    { id: 'evidence', label: 'Evidence', icon: '📸' },
    { id: 'scheduler', label: 'Scheduler', icon: '⏰' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />
      case 'targets':
        return <TargetsPage />
      case 'findings':
        return <FindingsPage />
      case 'reports':
        return <ReportsPage />
      case 'evidence':
        return <EvidencePage />
      case 'scheduler':
        return <SchedulerPage />
      case 'settings':
        return <SettingsPage />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-gray-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-green-400">AutoBounty OS</h1>
              <span className="ml-3 text-xs text-gray-400">v1.0.0</span>
            </div>
            <div className="flex space-x-1">
              {navigation.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setCurrentPage(item.id as Page)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    currentPage === item.id
                      ? 'bg-green-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderPage()}
      </main>

      <footer className="bg-gray-900 text-gray-400 py-4 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
          AutoBounty OS - Production-Grade Bug Bounty Automation Platform
        </div>
      </footer>
    </div>
  )
}

export default App

// src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New', monospace;
}

// src/services/apiClient.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export interface Target {
  id: number
  name: string
  handle: string
  url: string
  priority: number
  enabled: boolean
  platform: string
  last_recon?: string
  notes?: string
  created_at: string
}

export interface Finding {
  id: number
  target_id: number
  title: string
  severity: string
  status: string
  description?: string
  raw_data?: any
  created_at: string
}

export interface Evidence {
  id: number
  target_id: number
  finding_id?: number
  type: string
  file_path?: string
  meta?: any
  created_at: string
}

export interface Report {
  id: number
  target_id: number
  title: string
  status: string
  markdown: string
  severity: string
  submitted_to?: string
  finding_ids?: number[]
  created_at: string
  submitted_at?: string
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getTargets(): Promise<Target[]> {
    return this.request<Target[]>('/targets/')
  }

  async createTarget(data: Partial<Target>): Promise<Target> {
    return this.request<Target>('/targets/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateTarget(id: number, data: Partial<Target>): Promise<Target> {
    return this.request<Target>(`/targets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteTarget(id: number): Promise<void> {
    return this.request<void>(`/targets/${id}`, { method: 'DELETE' })
  }

  async getFindings(params?: { target_id?: number; severity?: string; status?: string }): Promise<Finding[]> {
    const query = new URLSearchParams(params as any).toString()
    return this.request<Finding[]>(`/findings/${query ? `?${query}` : ''}`)
  }

  async createFinding(data: Partial<Finding>): Promise<Finding> {
    return this.request<Finding>('/findings/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateFinding(id: number, data: Partial<Finding>): Promise<Finding> {
    return this.request<Finding>(`/findings/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getEvidence(params?: { target_id?: number; finding_id?: number }): Promise<Evidence[]> {
    const query = new URLSearchParams(params as any).toString()
    return this.request<Evidence[]>(`/evidence/${query ? `?${query}` : ''}`)
  }

  async captureEvidence(data: { url: string; target_id: number; finding_id?: number; capture_types: string[] }): Promise<any> {
    return this.request<any>('/evidence/capture', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getReports(params?: { target_id?: number; status?: string }): Promise<Report[]> {
    const query = new URLSearchParams(params as any).toString()
    return this.request<Report[]>(`/reports/${query ? `?${query}` : ''}`)
  }

  async createReport(data: Partial<Report>): Promise<Report> {
    return this.request<Report>('/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async generateReport(findingId: number): Promise<Report> {
    return this.request<Report>(`/reports/generate/${findingId}`, { method: 'POST' })
  }

  async updateReport(id: number, data: Partial<Report>): Promise<Report> {
    return this.request<Report>(`/reports/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async submitReport(id: number, platform: string = 'hackerone'): Promise<any> {
    return this.request<any>(`/reports/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ platform }),
    })
  }

  async runScheduler(): Promise<any> {
    return this.request<any>('/scheduler/run', { method: 'POST' })
  }

  async runTargetRecon(targetId: number): Promise<any> {
    return this.request<any>(`/scheduler/run/target/${targetId}`, { method: 'POST' })
  }

  async getConfig(): Promise<any> {
    return this.request<any>('/config/platform')
  }
}

export const apiClient = new ApiClient(API_BASE_URL)