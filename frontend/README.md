# Company Profile Dashboard

A modern React dashboard to display company profile data from Gemini AI.

## Features

- 📊 View comprehensive company profiles
- 🎨 Modern, responsive UI
- 📁 JSON file upload
- 🔍 Tab-based navigation (What, When, Where, How, Who, Sources)
- 📱 Mobile-friendly design

## Getting Started

### Install Dependencies

```bash
npm install
```

### Configure Environment Variables

Create a `.env` file in the `frontend` directory (or copy from `.env.example` if available):

```bash
# Backend API URL - Change port to match your backend (default: 9000)
VITE_API_URL=http://localhost:9000/api/v1

# Optional: WebSocket URL (will be derived from VITE_API_URL if not set)
# VITE_WS_URL=ws://localhost:9000/api/v1/ws
```

**Important:** If your backend is running on a different port (e.g., 9000), make sure to set `VITE_API_URL` accordingly.

### Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build for Production

```bash
npm run build
```

## Usage

1. Click "Select JSON File" button
2. Choose a `gemini_company_profile_*.json` file
3. View the company profile data in organized sections
4. Navigate between sections using tabs

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── CompanyProfile.jsx    # Main profile component
│   │   └── SectionCard.jsx       # Section display component
│   ├── App.jsx                    # Main app component
│   ├── main.jsx                   # Entry point
│   └── App.css                    # Main styles
├── index.html
└── package.json
```
