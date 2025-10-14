# MarkezardAI - AI-Powered Marketing Campaign Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

MarkezardAI is a production-grade AI-powered marketing platform that generates high-converting campaigns with untapped interest targeting, multi-platform publishing, and real-time analytics.

## 🚀 Features

- **AI-Powered Campaign Generation**: Generate compelling ad copy and creative instructions using Google Gemini AI
- **Untapped Interest Targeting**: Discover low-competition interests with proprietary success scoring (0-100)
- **Multi-Platform Publishing**: Deploy to Meta, Google, TikTok, LinkedIn with unified management
- **Website Integration**: Extract products from Shopify, WordPress, and custom sites
- **Real-Time Analytics**: Track performance metrics with live data insights
- **Secure Architecture**: Firebase Auth, API key rotation, audit logging
- **Production Ready**: Docker support, comprehensive testing, security scans

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   External      │
│   Frontend      │◄──►│   Backend       │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • React UI      │    │ • API Routes    │    │ • Gemini AI     │
│ • Auth Context  │    │ • AI Service    │    │ • Firebase      │
│ • Glassmorphism │    │ • Web Scraping  │    │ • Meta Ads      │
│ • Animations    │    │ • Campaign Mgmt │    │ • Shopify API   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Docker & Docker Compose** (optional)
- **Git** for version control

## 🔧 Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Frontend Environment Variables (Next.js)
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key_here
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abcdef123456
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000

# Backend Environment Variables (FastAPI)
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account","project_id":"your_project"}
GEMINI_API_KEY_1=your_gemini_api_key_1
GEMINI_API_KEY_2=your_gemini_api_key_2
GEMINI_API_KEY_3=your_gemini_api_key_3
GEMINI_API_KEY_4=your_gemini_api_key_4
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_123456789
ENVIRONMENT=development
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd markezardai

# Setup project (installs dependencies)
./run.sh setup  # Linux/Mac
# or
run.bat setup   # Windows

# Start development servers
./run.sh dev     # Linux/Mac
# or
run.bat dev      # Windows
```

### Option 2: Docker Compose

```bash
# Clone and start with Docker
git clone <repository-url>
cd markezardai
cp .env.example .env
# Edit .env with your API keys
docker-compose up --build
```

### Option 3: Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## 📱 Application URLs

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Schema**: http://localhost:8000/redoc

## 🧪 Testing

### Run All Tests
```bash
./run.sh test    # Linux/Mac
run.bat test     # Windows
```

### Backend Tests Only
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Tests Only
```bash
cd frontend
npm test
```

## 🔍 Code Quality & Security

### Run All Checks
```bash
./run.sh check   # Linux/Mac
run.bat check    # Windows
```

### Individual Checks
```bash
# Backend
cd backend
black . --check          # Code formatting
flake8 .                 # Linting
bandit -r app/           # Security scan
pip-audit                # Dependency audit

# Frontend
cd frontend
npm run lint             # ESLint
npm audit                # Dependency audit
```

## 🐳 Docker Deployment

### Development
```bash
docker-compose up --build
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up --build
```

### Individual Services
```bash
# Backend only
docker build -f Dockerfile.backend -t markezardai-backend .
docker run -p 8000:8000 markezardai-backend

# Frontend only
docker build -f Dockerfile.frontend -t markezardai-frontend .
docker run -p 3000:3000 markezardai-frontend
```

## 🌐 Deployment Options

### Vercel (Frontend)
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Render (Full Stack)
1. Create new Web Service for backend
2. Create new Static Site for frontend
3. Configure environment variables
4. Deploy

### Railway
1. Connect GitHub repository
2. Configure services for backend and frontend
3. Set environment variables
4. Deploy

### Google Cloud Platform
```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT_ID/markezardai-backend
gcloud run deploy --image gcr.io/PROJECT_ID/markezardai-backend --platform managed
```

## 📊 API Endpoints

### Authentication
- `POST /auth/verify-token` - Verify Firebase ID token

### Website Integration
- `POST /integrate-website` - Extract products from websites
- `POST /analyse-website` - AI analysis of website data
- `GET /platform-suggestions` - Get recommended ad platforms

### Campaign Management
- `POST /generate-campaign` - Generate AI-powered campaigns
- `POST /publish-campaign` - Publish campaigns (dry-run/live)
- `GET /campaign-analytics` - Retrieve campaign performance

### Health & Monitoring
- `GET /health` - Health check endpoint
- `GET /docs` - Interactive API documentation

## 🔐 Security Features

- **Firebase Authentication** with Google OAuth
- **API Key Rotation** for Gemini AI (up to 4 keys)
- **Dry-Run Safety** for campaign publishing
- **Input Validation** with Pydantic models
- **HTML Sanitization** for scraped content
- **Audit Logging** for all campaign actions
- **Rate Limiting** on publish endpoints
- **CORS Protection** with specific origins

## 🎯 Untapped Interest Targeting

MarkezardAI's core feature analyzes and scores interests based on:

- **Relevance Score** (0-100): Semantic match to product
- **Competition Level**: Low/Medium/High based on ad saturation
- **Success Probability**: AI-calculated likelihood of conversion
- **Market Signals**: Trend analysis and demand indicators

Example output:
```json
{
  "interest": "organic skincare",
  "success_score": 85,
  "competition": "low",
  "reasoning": "High search volume among young organic buyers + low ad saturation"
}
```

## 🔧 Configuration

### Gemini AI Setup
1. Get API keys from Google AI Studio
2. Add up to 4 keys for automatic rotation
3. Keys are used round-robin with failure handling

### Firebase Setup
1. Create Firebase project
2. Enable Authentication (Email + Google)
3. Create Firestore database
4. Download service account JSON

### Meta Ads Setup
1. Create Meta Developer account
2. Get system user access token
3. Configure ad account permissions
4. Test with dry-run mode first

## 📈 Monitoring & Analytics

### Health Checks
- Backend: `GET /health`
- Database connectivity
- External API status
- Memory and CPU usage

### Logging
- Structured JSON logs
- Request/response tracking
- Error monitoring
- Audit trail for campaigns

### Metrics
- Campaign performance (ROAS, CTR, CPC)
- API response times
- User engagement
- System resource usage

## 🛠️ Development

### Project Structure
```
markezardai/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── models/         # Pydantic models
│   │   ├── routers/        # API route handlers
│   │   └── services/       # Business logic
│   └── tests/              # Backend tests
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/           # App router pages
│   │   ├── components/    # React components
│   │   └── lib/           # Utilities and services
│   └── __tests__/         # Frontend tests
├── docker-compose.yml     # Docker orchestration
├── run.sh / run.bat      # Run scripts
└── README.md             # This file
```

### Adding New Features
1. Create feature branch
2. Add backend endpoint in `routers/`
3. Add frontend component in `components/`
4. Write tests for both
5. Update documentation
6. Submit pull request

### Database Schema (Firestore)
```
users/
  {uid}/
    email: string
    name: string
    plan: string
    created_at: timestamp

campaigns/
  {campaign_id}/
    user_id: string
    platform: string
    status: string
    created_at: timestamp
    performance: object

audit_logs/
  {log_id}/
    user_id: string
    event_type: string
    details: object
    timestamp: timestamp
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint for API reference
- **Issues**: Create GitHub issue with detailed description
- **Discussions**: Use GitHub Discussions for questions
- **Email**: support@markezardai.com (if applicable)

## 🔄 Changelog

### v1.0.0 (Current)
- Initial release with core features
- AI-powered campaign generation
- Multi-platform publishing
- Untapped interest targeting
- Website integration
- Comprehensive testing suite

## 🎯 Roadmap

- [ ] Additional ad platforms (TikTok, LinkedIn, X)
- [ ] Advanced analytics dashboard
- [ ] A/B testing capabilities
- [ ] Campaign templates
- [ ] Team collaboration features
- [ ] API rate limiting improvements
- [ ] Mobile app development

---

**Built with ❤️ using Next.js, FastAPI, and Google Gemini AI**
