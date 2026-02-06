import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';

function App() {
    const [target, setTarget] = useState('');
    const [scanning, setScanning] = useState(false);
    const [results, setResults] = useState<any>(null);

    const startScan = async () => {
        if (!target) return;
        setScanning(true);
        setResults(null);

        try {
            const response = await fetch('http://localhost:8002/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target, scan_type: 'quick' })
            });
            const data = await response.json();
            setResults(data);
        } catch (error) {
            console.error('Scan failed:', error);
            alert('Failed to connect to AutoBounty backend');
        } finally {
            setScanning(false);
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'high': return 'text-red-500 bg-red-100';
            case 'medium': return 'text-orange-500 bg-orange-100';
            case 'low': return 'text-yellow-600 bg-yellow-100';
            default: return 'text-gray-500 bg-gray-100';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 text-white p-8">
            <div className="max-w-5xl mx-auto">
                <header className="mb-12">
                    <h1 className="text-5xl font-bold mb-2 bg-gradient-to-r from-red-400 to-purple-500 bg-clip-text text-transparent">
                        AutoBounty
                    </h1>
                    <p className="text-gray-400 text-lg">Automated Bug Bounty & Vulnerability Scanner</p>
                </header>

                <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-8 border border-gray-700 mb-8">
                    <h2 className="text-2xl font-semibold mb-6">Start Security Scan</h2>

                    <div className="flex gap-4">
                        <input
                            type="text"
                            value={target}
                            onChange={(e) => setTarget(e.target.value)}
                            placeholder="Enter target URL or IP (e.g., example.com)"
                            className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-red-500"
                        />
                        <button
                            onClick={startScan}
                            disabled={scanning || !target}
                            className="bg-red-600 hover:bg-red-700 disabled:bg-gray-600 text-white font-semibold px-8 py-3 rounded-lg transition"
                        >
                            {scanning ? 'Scanning...' : 'Scan'}
                        </button>
                    </div>
                </div>

                {results && (
                    <div className="space-y-6">
                        <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-gray-700">
                            <h3 className="text-xl font-semibold mb-4">Scan Results</h3>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <p className="text-gray-400">Scan ID</p>
                                    <p className="font-mono">{results.scan_id}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400">Target</p>
                                    <p className="font-mono">{results.target}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400">Status</p>
                                    <p className="text-green-400 uppercase">{results.status}</p>
                                </div>
                                <div>
                                    <p className="text-gray-400">Vulnerabilities Found</p>
                                    <p className="text-2xl font-bold">{results.vulnerabilities?.length || 0}</p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-gray-800/50 backdrop-blur-sm rounded-lg p-6 border border-gray-700">
                            <h3 className="text-xl font-semibold mb-4">Discovered Vulnerabilities</h3>
                            <div className="space-y-4">
                                {results.vulnerabilities?.map((vuln: any) => (
                                    <div key={vuln.id} className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                                        <div className="flex items-start justify-between mb-2">
                                            <div>
                                                <h4 className="font-semibold text-lg">{vuln.title}</h4>
                                                <p className="text-gray-400 text-sm font-mono">{vuln.id}</p>
                                            </div>
                                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getSeverityColor(vuln.severity)}`}>
                                                {vuln.severity.toUpperCase()}
                                            </span>
                                        </div>
                                        <p className="text-gray-300 mb-2">{vuln.description}</p>
                                        {vuln.cve && (
                                            <p className="text-sm text-blue-400">CVE: {vuln.cve}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                <footer className="mt-12 text-center text-gray-500 text-sm">
                    <p>AutoBounty v1.0.0 - Automated Security Scanner</p>
                    <p className="mt-1">⚠️ For authorized testing only</p>
                </footer>
            </div>
        </div>
    );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
