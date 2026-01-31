# Hard Tech News Aggregator

A news aggregator that pulls the latest hard tech and deep tech startup news every time you open it.

## Topics Covered

- **Hard Tech / Deep Tech** - General hard tech startup news, funding, venture capital
- **Defense & Aerospace** - Defense technology, military startups (Anduril, Shield AI, etc.)
- **Energy & Nuclear** - Nuclear fusion, SMRs, clean energy, climate tech
- **Robotics** - Industrial automation, humanoid robots, robotics startups
- **Semiconductors** - Chip design, fab manufacturing, semiconductor startups
- **Biotech** - Synthetic biology, gene therapy, biotech funding
- **Space** - Launch vehicles, satellites, space technology
- **Manufacturing** - Advanced manufacturing, 3D printing, additive manufacturing
- **Quantum & Computing** - Quantum computing, photonics

## Usage

```bash
python server.py
```

This starts a local server and opens your browser to the news dashboard. The aggregator fetches fresh articles from all sources on each load.

### Requirements

- Python 3.6+ (standard library only, no pip install needed)

### Keyboard Shortcuts

- `/` - Focus the search/filter bar
- `Escape` - Clear search and unfocus

## How It Works

1. A lightweight Python HTTP server starts on a random free port
2. The browser opens automatically to the dashboard
3. The frontend calls `/api/news` which fetches RSS feeds in parallel
4. Articles are deduplicated, categorized, and sorted by date
5. Click any article card to open it in a new tab

## Sources

News is aggregated from:

- **Google News RSS** - Targeted searches for each hard tech category
- **TechCrunch** - Hardware section
- **IEEE Spectrum** - Engineering and technology
- **MIT Technology Review** - Emerging technology
- **SpaceNews** - Space industry
- **Ars Technica** - Science and technology
