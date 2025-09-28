# SIHP-IntelRisk

A comprehensive disaster intelligence platform with real-time hotspot monitoring, AI-powered analysis, and interactive mapping capabilities.

## 🚀 Quick Start

### Prerequisites
- Node.js (v18 or higher)
- npm or yarn
- PostgreSQL (optional - uses mock data by default)

### Development Setup

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd SIHP-IntelRisk
   ./start-dev.sh
   ```

2. **Manual Setup (Alternative)**
   ```bash
   # Backend
   cd Back-End
   npm install
   cp .env.example .env
   npm run dev
   
   # Frontend (in new terminal)
   cd Front-End
   npm install
   npm run dev
   ```

3. **Access the Application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:3001
   - API Documentation: http://localhost:3001/api/v1

### Default Login Credentials
- **Email**: ace@gmail.com
- **Password**: pass
- **Role**: Admin

## 🏗️ Architecture

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **Maps**: Leaflet with React-Leaflet
- **State Management**: React Context + Hooks
- **Routing**: React Router v7
- **Animations**: Framer Motion
- **Charts**: Recharts

### Backend (Node.js + Express)
- **Framework**: Express.js with TypeScript
- **Database**: PostgreSQL with connection pooling
- **Authentication**: JWT tokens
- **Validation**: Joi schema validation
- **Security**: Helmet, CORS, Rate limiting
- **File Upload**: Multer

## 🗺️ Features

### Interactive Map
- **Real-time Hotspots**: Dynamic disaster hotspot visualization
- **Leaflet Integration**: Professional mapping with OpenStreetMap
- **Custom Markers**: Severity-based color coding and event type icons
- **Interactive Popups**: Detailed hotspot information
- **Filtering**: Time range, severity, event type filters

### Dashboard
- **Live Monitoring**: Real-time disaster intelligence
- **Analytics**: Comprehensive charts and statistics
- **Fact Checker**: AI-powered content verification
- **Export**: JSON/CSV data export capabilities

### Authentication & Security
- **JWT Authentication**: Secure token-based auth
- **Role-based Access**: Admin, Analyst, Viewer roles
- **Rate Limiting**: API protection
- **Input Validation**: Comprehensive data validation

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/sihp_intelrisk
JWT_SECRET=your-secret-key
FRONTEND_URL=http://localhost:5173
```

**Frontend (.env)**
```env
VITE_API_BASE_URL=http://localhost:3001/api/v1
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - User logout

### Hotspots
- `GET /api/v1/hotspots/composite` - Get disaster hotspots
- `GET /api/v1/hotspots/composite/:id` - Get specific hotspot
- `POST /api/v1/hotspots/human` - Create human hotspot
- `GET /api/v1/hotspots/stats` - Get statistics

### Fact Checking
- `POST /api/v1/fact-check` - Submit content for verification
- `GET /api/v1/fact-check/:id` - Get verification result
- `GET /api/v1/fact-check` - Get verification history

### Export
- `GET /api/v1/export/json` - Export data as JSON
- `GET /api/v1/export/csv` - Export data as CSV

## 🛠️ Development

### Project Structure
```
SIHP-IntelRisk/
├── Front-End/          # React frontend
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── hooks/      # Custom hooks
│   │   ├── services/   # API services
│   │   └── types/      # TypeScript types
├── Back-End/           # Express backend
│   ├── src/
│   │   ├── config/     # Configuration
│   │   ├── middleware/ # Express middleware
│   │   ├── routes/     # API routes
│   │   └── services/   # Business logic
└── start-dev.sh       # Development startup script
```

### Key Technologies
- **Maps**: Leaflet for professional mapping
- **Real-time**: WebSocket connections for live updates
- **Security**: JWT authentication with role-based access
- **Database**: PostgreSQL with async operations
- **Validation**: Comprehensive input validation
- **Testing**: Jest and React Testing Library

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill processes on ports 3001 and 5173
   npx kill-port 3001 5173
   ```

2. **Database Connection Issues**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - App works with mock data if DB unavailable

3. **API Connection Issues**
   - Verify backend is running on port 3001
   - Check CORS configuration
   - Ensure .env files are properly configured

### Development Tips
- Use browser dev tools for debugging
- Check console for API errors
- Backend logs show detailed error information
- Mock data is used when API calls fail

## 📝 License

This project is licensed under the MIT License.