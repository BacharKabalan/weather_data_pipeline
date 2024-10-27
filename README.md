
# Weather Data Pipeline

A real-time data pipeline to fetch weather data, process it, and visualize it with Kafka, Flink, InfluxDB, and Grafana.

## Prerequisites
- Docker
- Python 3.8+
- API key from OpenWeather API

## Installation
1. Clone the repo: `git clone <repo_url>`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Docker containers with: `docker-compose up -d`

## Usage
- Fetch weather data: `python scripts/data_fetcher.py`
- Process data: Run Flink job in `scripts/data_processor.py`

