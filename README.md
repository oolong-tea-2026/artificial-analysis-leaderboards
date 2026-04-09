# Artificial Analysis Leaderboards

[![Daily Fetch](https://github.com/oolong-tea-2026/artificial-analysis-leaderboards/actions/workflows/fetch.yml/badge.svg)](https://github.com/oolong-tea-2026/artificial-analysis-leaderboards/actions/workflows/fetch.yml)

Daily snapshots of [Artificial Analysis](https://artificialanalysis.ai) AI model leaderboards via their official API.

## Data

| Endpoint | Description | Data |
|----------|-------------|------|
| `llms` | LLM benchmarks, pricing & speed (472+ models) | Intelligence index, coding index, math index, MMLU-Pro, GPQA, HLE, LiveCodeBench, pricing, tokens/sec |
| `text-to-image` | Text-to-image ELO rankings | ELO, rank, CI95, category breakdowns |
| `image-editing` | Image editing ELO rankings | ELO, rank, CI95 |
| `text-to-speech` | Text-to-speech ELO rankings | ELO, rank, CI95 |
| `text-to-video` | Text-to-video ELO rankings | ELO, rank, CI95, category breakdowns |
| `image-to-video` | Image-to-video ELO rankings | ELO, rank, CI95, category breakdowns |

## Structure

```
data/
├── latest.json          # → {"date": "2026-04-09", "path": "data/2026-04-09"}
├── 2026-04-09/
│   ├── _index.json      # Daily summary
│   ├── llms.json        # LLM leaderboard
│   ├── text-to-image.json
│   ├── image-editing.json
│   ├── text-to-speech.json
│   ├── text-to-video.json
│   └── image-to-video.json
```

## Quick Access

```bash
# Latest LLM data
curl -s https://raw.githubusercontent.com/oolong-tea-2026/artificial-analysis-leaderboards/main/data/latest.json

# Specific day
curl -s https://raw.githubusercontent.com/oolong-tea-2026/artificial-analysis-leaderboards/main/data/2026-04-09/llms.json
```

## Updates

Data fetched daily at 05:00 UTC via GitHub Actions. Source: [Artificial Analysis API](https://artificialanalysis.ai/api-reference).

## Attribution

Data provided by [Artificial Analysis](https://artificialanalysis.ai). See their [methodology](https://artificialanalysis.ai/methodology) for benchmark details.

## License

MIT — Data attribution to Artificial Analysis required.
