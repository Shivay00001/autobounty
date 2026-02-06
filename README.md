# 🎯 AutoBounty OS

**Professional-Grade Bug Bounty Automation Platform**

A complete, production-ready system for automating bug bounty reconnaissance, evidence capture, report generation, and vulnerability management. Built for solo security researchers and small teams.

![Version](https://img.shields.io/badge/version-1.0.0-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-18.2-61dafb.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.104-009688.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

---

## 🌟 Features

### 🔍 Automated Reconnaissance
- **Passive Scanning**: robots.txt, sitemaps, security headers, TLS info
- **Lightweight Crawling**: Discover endpoints with configurable depth
- **Change Detection**: Hash-based monitoring for new findings
- **Scheduled Scans**: Daily/weekly automated recon with APScheduler

### 📸 Evidence Capture Engine
- **Full-Page Screenshots**: Desktop and mobile views
- **Element Capture**: Target specific elements with CSS selectors
- **HTTP Responses**: Complete headers and body capture
- **Network Logs**: Browser performance and resource timing
- **Organized Storage**: Evidence linked to targets and findings

### 📊 Hunter Dashboard
- **Modern UI**: Clean, responsive interface inspired by HackerOne
- **Target Management**: Track multiple bug bounty programs
- **Finding Triage**: Categorize by severity, status, and target
- **Evidence Gallery**: Visual browser for captured screenshots
- **Report Builder**: Markdown-based report generation

### 📝 Report Generation
- **Auto-Generation**: Create reports from findings with one click
- **Customizable Templates**: Pre-built templates for common vulns
- **Markdown Editor**: Edit reports directly in the dashboard
- **Copy to Clipboard**: Quick export for manual submission
- **HackerOne Integration**: Direct API submission (when configured)

### 🔔 Notifications
- **Telegram**: Real-time alerts for new findings
- **Slack**: Team notifications with rich formatting
- **Severity-Based**: Filter notifications by criticality
- **Batch Updates**: Daily summaries of scan results

### 🏗️ Production Architecture
- **FastAPI Backend**: High-performance async API
- **React Frontend**: Modern TypeScript SPA
- **SQLAlchemy ORM**: Flexible database abstraction
- **Docker Compose**: One-command deployment
- **RESTful API**: Full documentation with OpenAPI/Swagger

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
- Docker & Docker Compose
- 8GB RAM minimum
- 20GB free disk space

# Optional (for local development)
- Python 3.11+
- Node.js 18+
- Chrome/Chromium browser
```

### Installation

**1. Clone or download the project structure**

**2. Configure environment**
```bash
cd backend
cp .env.example .env
# Edit .env with your API keys and settings
```

**3. Start all services**
```bash
docker-compose up --build
```

**4. Access the application**
- Dashboard: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**5. Initialize with sample data**
```bash
docker-compose exec backend python scripts/init_db.py
```

---

## 📖 Complete Documentation

See [SETUP.md](SETUP.md) for:
- Detailed installation instructions
- Local development setup (without Docker)
- Configuration guide for all integrations
- API endpoint reference
- Troubleshooting guide

---

## 🎯 Usage Workflow

### 1️⃣ Add a Target
```
Dashboard → Targets → + Add Target
Enter program details and enable watchlist
```

### 2️⃣ Run Reconnaissance
```
Targets → Run Recon (manual)
OR
Scheduler → Run Scheduler Now (all targets)
```

### 3️⃣ Review Findings
```
Findings → Filter by severity/status
Click finding to view details
Update status: Open → Triaged → Reported
```

### 4️⃣ Capture Evidence
```
Evidence → + Capture Evidence
Enter URL, select capture types
Screenshots and logs saved automatically
```

### 5️⃣ Generate Report
```
Findings → Select finding → Report
Edit markdown as needed
Copy or submit directly to H1
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Dashboard │ Targets │ Findings │ Reports │ Evidence   │
└─────────────────────┬───────────────────────────────────┘
                      │ REST API
┌─────────────────────┴───────────────────────────────────┐
│                   Backend (FastAPI)                      │
├──────────────────────────────────────────────────────────┤
│  Routes │ Services │ Models │ Schemas │ Workers         │
├──────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌──────────────┐  ┌─────────────┐    │
│  │  Evidence  │  │    Recon     │  │  Scheduler  │    │
│  │   Engine   │  │   Service    │  │   Worker    │    │
│  └────────────┘  └──────────────┘  └─────────────┘    │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────┐
│         Database (SQLite/PostgreSQL)                     │
│  Targets │ Findings │ Evidence │ Reports                │
└──────────────────────────────────────────────────────────┘
```

---

## 🔧 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation using Python type hints
- **Selenium**: Browser automation for screenshots
- **BeautifulSoup**: HTML parsing for crawling
- **APScheduler**: Background job scheduling
- **Requests**: HTTP client for API calls

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Fetch API**: HTTP client for backend communication

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Selenium Grid**: Distributed browser automation
- **SQLite/PostgreSQL**: Database options

---

## 📊 API Endpoints

### Targets
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/targets/` | List all targets |
| POST | `/api/targets/` | Create new target |
| GET | `/api/targets/{id}` | Get target details |
| PUT | `/api/targets/{id}` | Update target |
| DELETE | `/api/targets/{id}` | Delete target |

### Findings
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/findings/` | List findings (filterable) |
| POST | `/api/findings/` | Create finding |
| PUT | `/api/findings/{id}` | Update finding |
| DELETE | `/api/findings/{id}` | Delete finding |

### Evidence
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/evidence/` | List evidence |
| POST | `/api/evidence/capture` | Capture new evidence |
| DELETE | `/api/evidence/{id}` | Delete evidence |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/` | List reports |
| POST | `/api/reports/` | Create report |
| POST | `/api/reports/generate/{finding_id}` | Auto-generate from finding |
| PUT | `/api/reports/{id}` | Update report |
| POST | `/api/reports/{id}/submit` | Submit to platform |
| DELETE | `/api/reports/{id}` | Delete report |

### Scheduler
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scheduler/status` | Get scheduler status |
| POST | `/api/scheduler/run` | Run manually |
| POST | `/api/scheduler/run/target/{id}` | Run for specific target |

Full API documentation available at `/docs` when running.

---

## 🔐 Security Considerations

### For Development
- SQLite database for simplicity
- Default secret keys (change in production!)
- CORS enabled for localhost
- Debug mode enabled

### For Production
1. **Use strong secrets**: Generate with `openssl rand -hex 32`
2. **PostgreSQL database**: Better concurrency and performance
3. **Disable debug mode**: Set `DEBUG=False`
4. **Restrict CORS**: Only allow your frontend domain
5. **Use HTTPS**: Set up SSL/TLS certificates
6. **API authentication**: Implement auth middleware
7. **Rate limiting**: Add rate limits to API endpoints
8. **Input validation**: All inputs validated with Pydantic
9. **Secure storage**: Evidence files served with authentication

---

## 🐛 Common Issues & Solutions

### Chrome/Selenium Issues
```bash
# Solution 1: Use Docker (recommended)
docker-compose up chrome

# Solution 2: Install Chrome locally
# Ubuntu/Debian
sudo apt-get install chromium-browser chromium-chromedriver

# macOS
brew install --cask google-chrome
brew install chromedriver
```

### Database Issues
```bash
# Reset database
rm backend/autobounty.db
docker-compose exec backend python scripts/init_db.py
```

### CORS Errors
```bash
# Add your frontend URL to backend/.env
CORS_ORIGINS=http://localhost:3000,http://your-frontend-url
```

---

## 📈 Roadmap

### Completed ✅
- Full-stack application with React + FastAPI
- Automated evidence capture engine
- Passive reconnaissance with change detection
- Scheduled scans with notifications
- Report generation and H1 integration
- Docker containerization
- Modern dashboard UI

### Future Enhancements 🚀
- [ ] Active scanning capabilities
- [ ] Plugin system for custom scanners
- [ ] Multi-user support with authentication
- [ ] Advanced reporting with PDF export
- [ ] Integration with more platforms (Bugcrowd, YesWeHack)
- [ ] AI-powered vulnerability classification
- [ ] Collaborative features for teams
- [ ] Mobile app for notifications
- [ ] GraphQL API option

---

## 🤝 Contributing

This is a complete, production-ready system. Contributions are welcome!

### Development Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Code Style
- **Backend**: Black formatter, type hints, docstrings
- **Frontend**: ESLint, Prettier, TypeScript strict mode
- **Commits**: Conventional commits format

---

## 📝 License

MIT License - feel free to use this for your bug bounty hunting!

---

## 🙏 Acknowledgments

Built with modern best practices for security researchers by security researchers.

Special thanks to:
- HackerOne for the platform API
- The bug bounty community for inspiration
- Open source projects that made this possible

---

## 📞 Support

- **Documentation**: See SETUP.md for detailed guides
- **Issues**: Report bugs or request features via issues
- **Security**: Report security issues privately

---

## 🎓 Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [HackerOne API Docs](https://api.hackerone.com/docs/v1)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

**Built with ❤️ for the bug bounty community**

**AutoBounty OS v1.0.0** - Your automated security research companion