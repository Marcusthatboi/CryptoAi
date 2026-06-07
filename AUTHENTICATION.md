# User Authentication & Account System Setup

## Overview

CryptoAI now includes a complete user authentication system with MongoDB integration. Users can create accounts, login with JWT tokens, and their portfolios and investments are stored in MongoDB.

## Features

✅ User Registration with email
✅ JWT-based Authentication  
✅ Secure Password Hashing (bcrypt)
✅ MongoDB User Profiles
✅ User Portfolio Management
✅ Protected Routes (Frontend)
✅ Role-based Access Control (Backend)
✅ Demo Admin Account

## Quick Start

### 1. Start MongoDB

Make sure MongoDB is running on your local machine:

```bash
# On Windows
mongod

# On macOS/Linux
brew services start mongodb-community

# Or use Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 2. Install Dependencies

```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Initialize Admin User

Run the initialization script to create the default admin account:

```bash
python init_admin.py
```

Output:
```
✅ Admin user created successfully!
   Username: Admin
   Password: Admin1
```

### 4. Start the Application

**Terminal 1 - Backend:**
```bash
python backend/main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 5. Access the Application

- **Frontend**: http://localhost:3000 (or port shown in terminal)
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## Demo Credentials

```
Username: Admin
Password: Admin1
```

## Authentication Flow

### Registration

```http
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "password": "securepassword123",
  "email": "john@example.com"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "username": "john_doe",
  "user_id": "507f1f77bcf86cd799439011",
  "expires_in": 86400
}
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "Admin",
  "password": "Admin1"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "username": "Admin",
  "user_id": "507f1f77bcf86cd799439012",
  "expires_in": 86400
}
```

### Get User Profile

```http
GET /auth/profile
Authorization: Bearer {access_token}

Response:
{
  "user_id": "507f1f77bcf86cd799439012",
  "username": "Admin",
  "email": "admin@cryptoai.com",
  "created_at": "2026-05-31T12:00:00.000Z",
  "updated_at": "2026-05-31T12:00:00.000Z"
}
```

## Portfolio API

### Get User Portfolio

```http
GET /api/user/portfolio
Authorization: Bearer {access_token}

Response:
{
  "total_value": 100000.0,
  "cash": 95000.0,
  "holdings": [
    {
      "symbol": "BTC",
      "quantity": 0.1,
      "price": 50000.0,
      "total_value": 5000.0
    }
  ],
  "last_updated": "2026-05-31T12:00:00.000Z"
}
```

### Record Investment

```http
POST /api/user/portfolio/invest
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "symbol": "BTC",
  "quantity": 0.1,
  "price": 50000.0,
  "total_value": 5000.0
}

Response:
{
  "status": "success",
  "message": "Investment recorded: BTC",
  "portfolio": {...}
}
```

## Frontend Authentication

### Login Page

- **Route**: `/login`
- **Components**: LoginPage.jsx, LoginPage.css
- **Demo Credentials**: Admin / Admin1

### Register Page

- **Route**: `/register`
- **Components**: RegisterPage.jsx, LoginPage.css (shared styles)

### Protected Routes

All dashboard routes are protected with `ProtectedRoute` component:

```jsx
<ProtectedRoute>
  <Dashboard />
</ProtectedRoute>
```

Unauthenticated users are redirected to `/login`.

### Authentication Context Hook

Use the `useAuth` hook in any component:

```jsx
import { useAuth } from './hooks/useAuth'

export default function MyComponent() {
  const { user, token, login, logout } = useAuth()
  
  return (
    <div>
      {user && <p>Welcome, {user.username}!</p>}
    </div>
  )
}
```

## MongoDB Collections

### Users Collection

```javascript
{
  _id: ObjectId,
  username: "Admin",
  password: "$2b$12$...", // bcrypt hash
  email: "admin@cryptoai.com",
  created_at: "2026-05-31T12:00:00.000Z",
  updated_at: "2026-05-31T12:00:00.000Z",
  is_active: true,
  portfolio: {
    total_value: 100000.0,
    cash: 100000.0,
    holdings: [
      {
        symbol: "BTC",
        quantity: 0.1,
        price: 50000.0,
        total_value: 5000.0,
        created_at: "2026-05-31T12:00:00.000Z",
        updated_at: "2026-05-31T12:00:00.000Z"
      }
    ],
    last_updated: "2026-05-31T12:00:00.000Z"
  },
  settings: {
    theme: "dark",
    notifications: true,
    default_currency: "USD"
  }
}
```

## Environment Variables

Update `.env` file:

```
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DB_NAME=cryptoai

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Alpaca
ALPACA_API_KEY=PKLXQIDU6EY3HXAV2UGSMLELZL
ALPACA_SECRET_KEY=2qZ6ZTRNesVaCcXdjfNkzTmpK8HzeEQXTo21scPmSw9g

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
```

## Security Features

1. **Password Hashing**: bcrypt with configurable cost factor
2. **JWT Tokens**: Secure token-based authentication
3. **Token Expiration**: Configurable expiration time (default: 24 hours)
4. **MongoDB Indexes**: Unique username index for data integrity
5. **Protected Routes**: Client-side route protection with ProtectedRoute component
6. **Authorization Middleware**: Server-side authentication requirement

## Creating Additional Users

### Via Frontend

1. Go to http://localhost:3000/register
2. Fill in username, password, and email (optional)
3. Click "Register"
4. Automatically logged in after successful registration

### Via Script

Edit and run the following:

```python
import asyncio
from backend.auth import create_user
from backend.db import get_db

async def create_demo_user():
    db = await get_db()
    user = await create_user(
        db,
        username="demo_user",
        password="password123",
        email="demo@example.com"
    )
    print(f"Created user: {user['username']}")

asyncio.run(create_demo_user())
```

### Via MongoDB Client

```javascript
db.users.insertOne({
  "username": "newuser",
  "password": "$2b$12$...", // bcrypt hash
  "email": "new@example.com",
  "created_at": new Date(),
  "updated_at": new Date(),
  "is_active": true,
  "portfolio": {
    "total_value": 100000,
    "cash": 100000,
    "holdings": [],
    "last_updated": new Date()
  },
  "settings": {
    "theme": "dark",
    "notifications": true,
    "default_currency": "USD"
  }
})
```

## Troubleshooting

### "Username already exists"
- Use a different username
- Or delete the user from MongoDB: `db.users.deleteOne({username: "Admin"})`

### "Invalid authentication credentials"
- Check username and password are correct
- Verify user exists in MongoDB

### "MongoDB connection refused"
- Start MongoDB service
- Check MONGODB_URL in .env file

### Token expired
- Login again to get a new token
- Tokens are valid for 24 hours (configurable)

### Protected routes redirecting to login
- Check localStorage for `token` and `user_id`
- Clear browser cache and localStorage if needed
- Re-login to get a fresh token

## Next Steps

1. Customize user profile fields as needed
2. Add two-factor authentication (2FA)
3. Implement refresh token rotation
4. Add user preferences/settings management
5. Implement account deletion/archiving
6. Add password reset functionality
7. Implement social authentication (OAuth)

## File Structure

```
backend/
├── auth.py                 # Authentication module
└── main.py                 # Updated with auth endpoints

frontend/src/
├── pages/
│   ├── LoginPage.jsx       # Login page component
│   ├── RegisterPage.jsx    # Registration page component
│   └── LoginPage.css       # Authentication styles
├── hooks/
│   └── useAuth.js          # Authentication context hook
└── App.jsx                 # Updated with auth routes

root/
└── init_admin.py           # Initialize admin user script
```

## Support

For issues or questions about the authentication system, check:

1. Backend logs in terminal
2. Browser console (F12)
3. MongoDB logs
4. Network tab in DevTools (check API responses)
