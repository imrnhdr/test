# Hard Tech News Aggregator

A news aggregator that pulls the latest hard tech and deep tech startup news every time you open it. Works on any device with a browser — iPad, phone, or desktop.

## Usage

**Option 1 — GitHub Pages (iPad / any device):**

Visit the hosted page (enable GitHub Pages on this repo pointing to the branch root).

**Option 2 — Open locally:**

Open `index.html` directly in any browser. It fetches news client-side via CORS proxy.

**Option 3 — Python server (desktop):**

```bash
python server.py
```

Starts a local server and opens the dashboard. Faster and more reliable since feeds are fetched server-side.

## Topics Covered

- **Hard Tech / Deep Tech** - Startup news, funding, venture capital
- **Defense & Aerospace** - Defense technology, military startups (Anduril, Shield AI, etc.)
- **Energy & Nuclear** - Nuclear fusion, SMRs, clean energy, climate tech
- **Robotics** - Industrial automation, humanoid robots, robotics startups
- **Semiconductors** - Chip design, fab manufacturing, semiconductor startups
- **Biotech** - Synthetic biology, gene therapy, biotech funding
- **Space** - Launch vehicles, satellites, space technology
- **Manufacturing** - Advanced manufacturing, 3D printing, additive manufacturing
- **Quantum & Computing** - Quantum computing, photonics

## How It Works

1. On load, fetches RSS feeds from Google News and tech publications
2. Articles are deduplicated, categorized, and sorted newest-first
3. Filter by category tabs or search by keyword
4. Click any card to read the full article

## Sources

- **Google News RSS** - Targeted searches for each hard tech category
- **TechCrunch** - Hardware section
- **IEEE Spectrum** - Engineering and technology
- **MIT Technology Review** - Emerging technology
- **SpaceNews** - Space industry
- **Ars Technica** - Science and technology
