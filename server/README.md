# SIEM Server

Central Security Hub for Monitoring & Compliance - API Server that receives requests and forwards them to the complete disaster intelligence pipeline.

## 🚀 Quick Start

### 1. Start the Server

```bash
cd server
python start_server.py
```

The server will start on `http://localhost:8000`

### 2. Test the Server

```bash
python test_server.py
```

### 3. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 API Endpoints

### Health Check
- **GET** `/health` - Check server status
- **GET** `/` - Basic health check

### Core Functionality
- **POST** `/analyze` - Full pipeline analysis (extract → verify → detect hotspots)
- **POST** `/extract` - Extract reports only (for testing)

### Utilities
- **GET** `/stats` - Server statistics

## 📝 Request Format

### Analyze Request
```json
{
  "text": "Heavy flooding reported in Chennai last night. Water levels rising rapidly.",
  "source": "user_input"
}
```

### Response Format
```json
{
  "success": true,
  "reports": [
    {
      "event_type": "flood",
      "location": "Chennai",
      "timestamp": "2025-09-21T21:00:00+05:30",
      "description": "Heavy flooding reported...",
      "source": "news",
      "confidence": 1.0,
      "veracity_flag": "confirmed"
    }
  ],
  "hotspots": [
    {
      "location": "Chennai",
      "coordinates": [13.0827, 80.2707],
      "severity": "high",
      "event_count": 1,
      "risk_level": "high"
    }
  ],
  "verified_reports": [...],
  "message": "Successfully processed 1 disaster reports"
}
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Keys (required for full functionality)
PERPLEXITY_API_KEY=your_perplexity_key_here
GOOGLE_API_KEY=your_google_key_here

# Database (if using database features)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Redis (for caching)
REDIS_URL=redis://localhost:6379
```

### Required Dependencies

Install dependencies:
```bash
pip install -r requirements.txt
```

## 🧪 Testing

### Manual Testing

1. **Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Extract Test**:
   ```bash
   curl -X POST http://localhost:8000/extract \
     -H "Content-Type: application/json" \
     -d '{"text": "Flood in Mumbai today", "source": "test"}'
   ```

3. **Full Analysis**:
   ```bash
   curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "Heavy flooding in Chennai with water levels rising rapidly", "source": "test"}'
   ```

### Automated Testing

Run the complete test suite:
```bash
python test_server.py
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SIEM Server   │───▶│   ExtractorA     │───▶│   CheckerA      │
│   (FastAPI)     │    │   (Perplexity    │    │   (Verify &     │
│                 │    │    + Gemini)     │    │   Filter)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   DetecterA      │
                       │   (Generate      │
                       │    Hotspots)     │
                       └──────────────────┘
```

### Pipeline Flow

1. **Input Reception**: Server receives text input via API
2. **Report Extraction**: ExtractorA processes text using LLMs
3. **Report Verification**: CheckerA verifies and filters reports
4. **Hotspot Detection**: DetecterA generates disaster hotspots
5. **Response Generation**: Server returns complete analysis

## 📊 Features

- ✅ **Multi-LLM Support**: Perplexity API + Gemini fallback
- ✅ **Real-time Processing**: Async pipeline processing
- ✅ **Hotspot Generation**: Geographic clustering of events
- ✅ **Report Verification**: Source credibility and clustering
- ✅ **API Documentation**: Auto-generated Swagger/ReDoc
- ✅ **Health Monitoring**: Built-in health checks
- ✅ **Error Handling**: Comprehensive error management
- ✅ **CORS Support**: Cross-origin request handling

## 🔍 Monitoring

### Health Endpoints
- `/health` - Detailed component status
- `/stats` - Server statistics
- `/metrics` - Prometheus metrics (if configured)

### Logging
All requests and processing steps are logged with timestamps and details.

## 🚨 Troubleshooting

### Common Issues

1. **"Server components not initialized"**
   - Check API keys in `.env` file
   - Ensure all dependencies are installed

2. **"No reports extracted"**
   - Verify input text contains disaster-related content
   - Check LLM API connectivity

3. **"Hotspot detection failed"**
   - Ensure location data is extractable from text
   - Check geocoding service availability

### Debug Mode

Run with debug logging:
```bash
export LOG_LEVEL=DEBUG
python start_server.py
```

## 📈 Performance

- **Concurrent Processing**: Async pipeline handles multiple requests
- **Caching**: LRU cache for geocoding requests
- **Rate Limiting**: Built-in API rate limiting
- **Metrics**: Prometheus metrics for monitoring

## 🔒 Security

- Input validation using Pydantic models
- Rate limiting with SlowAPI
- CORS configuration for cross-origin requests
- Environment variable configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
