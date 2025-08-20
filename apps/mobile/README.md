# Fullstack Monolith Mobile App

A comprehensive React Native mobile application for the Fullstack Monolith platform, providing blog management, content creation, and community engagement features.

## Features

### 🔐 Authentication & Security
- JWT token-based authentication with automatic refresh
- Biometric authentication (Face ID, Touch ID, Fingerprint)
- Multi-factor authentication support
- OAuth2 social login integration
- Secure session management

### 📱 Core Functionality
- **Blog Management**: Create, edit, and manage blog posts
- **Real-time Comments**: Engage with community through comments
- **Search & Discovery**: Advanced search with filters
- **Notifications**: Push notifications for real-time updates
- **Analytics**: Track post performance and engagement
- **Offline Support**: Read content offline with automatic sync

### 🎨 User Experience
- Modern Material Design 3 UI
- Dark/Light theme support
- Smooth animations with Lottie
- Responsive design for all screen sizes
- Accessibility compliance
- Intuitive navigation with bottom tabs

### 🔧 Technical Features
- **State Management**: Zustand for client state, React Query for server state
- **API Integration**: Shared API client with the web application
- **Offline Capabilities**: Smart caching and offline data management
- **Performance**: Optimized with Fast Image, lazy loading, and code splitting
- **Testing**: Comprehensive test suite with Jest and React Native Testing Library
- **Code Quality**: ESLint, Prettier, and TypeScript for code quality

## Architecture

### Project Structure
```
apps/mobile/
├── src/
│   ├── components/          # Reusable UI components
│   ├── screens/            # Screen components
│   │   ├── auth/           # Authentication screens
│   │   ├── main/           # Main app screens
│   │   └── onboarding/     # Onboarding flow
│   ├── navigation/         # Navigation configuration
│   ├── services/           # API and business logic services
│   ├── store/              # State management (Context API)
│   ├── hooks/              # Custom React hooks
│   ├── config/             # App configuration
│   ├── types/              # TypeScript type definitions
│   ├── assets/             # Static assets (images, animations)
│   └── __tests__/          # Test files
├── android/                # Android-specific code
├── ios/                    # iOS-specific code
└── package.json
```

### Key Dependencies
- **React Native 0.73.2**: Latest stable version
- **React Navigation 6**: Navigation library
- **React Native Paper**: Material Design components
- **React Query**: Server state management
- **Zustand**: Client state management
- **React Native Reanimated**: Smooth animations
- **React Native Gesture Handler**: Touch gestures
- **Lottie React Native**: Vector animations
- **React Native Fast Image**: Optimized image loading
- **React Native Biometrics**: Biometric authentication
- **Firebase**: Push notifications and analytics

## Getting Started

### Prerequisites
- Node.js 18+ and npm 9+
- React Native CLI
- Android Studio (for Android development)
- Xcode (for iOS development)
- Java Development Kit (JDK) 11+

### Installation

1. **Install dependencies**:
   ```bash
   cd apps/mobile
   npm install
   ```

2. **iOS Setup** (macOS only):
   ```bash
   cd ios && pod install && cd ..
   ```

3. **Android Setup**:
   - Ensure Android SDK is installed
   - Create a virtual device in Android Studio

### Development

1. **Start Metro bundler**:
   ```bash
   npm start
   ```

2. **Run on Android**:
   ```bash
   npm run android
   ```

3. **Run on iOS** (macOS only):
   ```bash
   npm run ios
   ```

### Available Scripts

- `npm start` - Start Metro bundler
- `npm run android` - Run on Android device/emulator
- `npm run ios` - Run on iOS device/simulator
- `npm test` - Run test suite
- `npm run test:watch` - Run tests in watch mode
- `npm run test:coverage` - Run tests with coverage report
- `npm run lint` - Run ESLint
- `npm run lint:fix` - Fix ESLint issues
- `npm run format` - Format code with Prettier
- `npm run type-check` - Run TypeScript type checking
- `npm run build:android` - Build Android APK
- `npm run build:ios` - Build iOS archive
- `npm run clean` - Clean build artifacts

## Configuration

### Environment Variables
Create environment-specific configuration files:
- `.env.development` - Development environment
- `.env.staging` - Staging environment
- `.env.production` - Production environment

### API Configuration
Update `src/config/constants.ts` with your API endpoints:
```typescript
export const API_CONFIG = {
  BASE_URL: process.env.API_BASE_URL || 'http://localhost:8000/api',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
};
```

### Firebase Configuration
1. Add `google-services.json` to `android/app/`
2. Add `GoogleService-Info.plist` to `ios/`
3. Configure Firebase project settings

## Testing

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- --testPathPattern=HomeScreen
```

### Test Structure
- **Unit Tests**: Component and utility function tests
- **Integration Tests**: API and service integration tests
- **E2E Tests**: End-to-end user flow tests with Detox

### Writing Tests
```typescript
import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import { HomeScreen } from '../HomeScreen';

describe('HomeScreen', () => {
  it('renders welcome message', () => {
    const { getByText } = render(<HomeScreen />);
    expect(getByText(/Welcome back/)).toBeTruthy();
  });
});
```

## Building for Production

### Android
```bash
# Generate signed APK
npm run build:android

# Generate AAB for Play Store
cd android && ./gradlew bundleRelease
```

### iOS
```bash
# Build for App Store
npm run build:ios

# Or use Xcode for more control
open ios/MobileApp.xcworkspace
```

## Performance Optimization

### Bundle Size Optimization
- Code splitting with dynamic imports
- Tree shaking for unused code elimination
- Image optimization with WebP format
- Font subsetting for reduced font file sizes

### Runtime Performance
- Lazy loading for screens and components
- Image caching with React Native Fast Image
- Efficient list rendering with FlatList
- Memory leak prevention with proper cleanup

### Network Optimization
- Request/response caching
- Offline-first architecture
- Request deduplication
- Optimistic updates

## Deployment

### Code Push (Over-the-Air Updates)
```bash
# Install CodePush CLI
npm install -g code-push-cli

# Deploy update
code-push release-react MobileApp-iOS ios
code-push release-react MobileApp-Android android
```

### App Store Deployment
1. Build production version
2. Upload to App Store Connect
3. Submit for review
4. Release to users

### Google Play Deployment
1. Generate signed AAB
2. Upload to Google Play Console
3. Submit for review
4. Release to production

## Troubleshooting

### Common Issues

**Metro bundler issues**:
```bash
npm run reset-cache
```

**Android build issues**:
```bash
cd android && ./gradlew clean && cd ..
npm run clean
```

**iOS build issues**:
```bash
cd ios && pod install && cd ..
npm run clean:ios
```

**Package conflicts**:
```bash
rm -rf node_modules package-lock.json
npm install
```

### Debug Tools
- **Flipper**: React Native debugging platform
- **React Native Debugger**: Standalone debugging app
- **Chrome DevTools**: Network and performance debugging

## Contributing

### Code Style
- Follow TypeScript best practices
- Use ESLint and Prettier configurations
- Write comprehensive tests for new features
- Follow React Native performance guidelines

### Pull Request Process
1. Create feature branch from `main`
2. Implement changes with tests
3. Run linting and tests
4. Submit pull request with description
5. Address review feedback

## Security

### Best Practices
- Store sensitive data in Keychain/Keystore
- Use HTTPS for all API communications
- Implement certificate pinning
- Validate all user inputs
- Use biometric authentication when available

### Security Auditing
```bash
# Check for vulnerabilities
npm audit

# Fix vulnerabilities
npm audit fix
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

---

Built with ❤️ using React Native and TypeScript