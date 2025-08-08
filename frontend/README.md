# My Next.js PWA

A Progressive Web App built with Next.js, featuring Zustand state management, Axios API integration, and modern UI design.

## 🚀 Features

- **Progressive Web App (PWA)**: Installable on mobile and desktop devices
- **Zustand State Management**: Lightweight and efficient state management
- **Axios API Integration**: Configured with interceptors for authentication
- **TypeScript**: Full type safety throughout the application
- **Tailwind CSS**: Modern, utility-first CSS framework
- **Responsive Design**: Works perfectly on all device sizes

## 📁 Project Structure

```
my-app/
├── pages/                    # Next.js Pages Router
│   ├── index.tsx            # Main page with state management demo
│   ├── _app.tsx             # App root with PWA meta tags
│   └── api/                 # API routes
│       └── hello.ts         # Example API endpoint
├── components/              # Reusable components
│   ├── ApiTest.tsx         # API testing component
│   └── InstallPrompt.tsx   # PWA install prompt
├── store/                   # Zustand state management
│   └── index.ts            # Main store with counter logic
├── utils/                   # Utility functions
│   └── axios.ts            # Axios instance with interceptors
├── public/                  # Static assets
│   └── icons/              # PWA icons
├── styles/                  # Global styles
│   └── globals.css         # Tailwind CSS and custom styles
├── manifest.json           # PWA manifest
├── service-worker.js       # Service worker for offline support
└── next.config.js         # Next.js configuration with PWA
```

## 🛠️ Getting Started

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Run the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📱 PWA Features

- **Installable**: Add to home screen on mobile and desktop
- **Offline Support**: Service worker caches essential resources
- **App-like Experience**: Standalone mode without browser UI
- **Fast Loading**: Optimized for performance

## 🔧 State Management

The app uses Zustand for state management with a simple counter example:

```typescript
const { count, increment, decrement, reset } = useAppStore()
```

## 🌐 API Integration

Axios is configured with:
- Request/response interceptors
- Authentication token handling
- Error handling
- Base URL configuration

## 🎨 Styling

Built with Tailwind CSS for:
- Responsive design
- Modern UI components
- Consistent spacing and colors
- Dark mode support

## 📦 Build and Deploy

```bash
# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

## 🚀 Deployment

This PWA can be deployed to:
- Vercel (recommended)
- Netlify
- Any static hosting service

The service worker and manifest will be automatically generated during the build process.

## 📄 License

MIT License - feel free to use this project as a starting point for your own PWA!
