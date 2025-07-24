# Robo‑Pilot MAX

All‑in‑one, dual‑mode trading autopilot for turning **\$5,000** on thinkorswim® into consistent income or aggressive growth—your choice.

---

## 🚀 Features

* **Income Mode**: Diversified strategies (iron condors, credit spreads, covered calls) for steady monthly income.
* **Turbo Mode**: High‑frequency 0‑DTE trades on SPY for maximum growth potential.
* **Risk Fence**: Blocks trades if daily or per‑trade risk thresholds are breached.
* **Self‑Restart Watchdog**: Monitors service health and auto‑restarts on failure with cloud + local failover.
* **Smarter Filters**: ML‑powered edge filter, news/event skip, circuit breaker (>2% SPY move).
* **Dynamic Sizing & Turbo‑Compound**: Auto adjusts position size based on performance and streaks.
* **Dashboard & Controls**: Next.js dashboard with traffic‑light status, quick controls, mobile alerts.
* **AI Journal & Reports**: Auto‑generated PDF reports and AI‑summarized trade notes.

---

## 📦 Prerequisites

* Docker Desktop (Apple Silicon or use Colima)
* [Fly.io CLI](https://fly.io) (for cloud deployment)
* Node.js ≥18 (for local UI dev)
* Python 3.11 (for local backend dev)

---

## ⚙️ Installation

```bash
# Clone the repo
git clone https://github.com/you/robo-pilot-max.git
cd robo-pilot-max

# (Optional) Local development:
# Backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn core.core_api:app --reload

# Frontend
cd ui
npm install
npm run dev
```

---

## 🐳 Running with Docker

```bash
# Build and start all services
docker compose up --build -d

# Check logs
docker compose logs -f bot
docker compose logs -f ui

# Stop services
docker compose down
```

**Tip:** To rebuild only one service:

````bash
docker compose up --no-deps --build -d bot
``` or `-d ui`

---

## 🔧 Configuration

Edit `.env` for these key settings:

```dotenv
CLIENT_ID=...
CLIENT_SECRET=...
ACCOUNT_ID=...
REFRESH_TOKEN=...
MODE=income        # or turbo
RISK_DAILY=0.06
RISK_PER_TRADE=0.01
# ...see .env.example for full options
````

---

## 📁 Project Structure

```
robo-pilot-max/
├── core/         # Python backend (strategies, API, watcher, models)
├── ui/           # Next.js dashboard (App Router, TS)
├── backtest/     # Historical back‑testing scripts/data
├── infra/        # Deployment scripts & configs
├── docker-compose.yml
├── Dockerfile    # Python service
├── ui/Dockerfile # Next.js service
├── .env.example
└── README.md
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch (`git checkout -b feature/xyz`)
3. Make your changes & tests
4. Commit (`git commit -m "Add xyz"`)
5. Push (`git push origin feature/xyz`)
6. Open a Pull Request

---

## **📜 License**

**MIT © Your Name**
