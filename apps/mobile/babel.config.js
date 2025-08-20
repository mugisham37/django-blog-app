module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    [
      'module-resolver',
      {
        root: ['./src'],
        alias: {
          '@': './src',
          '@components': './src/components',
          '@screens': './src/screens',
          '@navigation': './src/navigation',
          '@services': './src/services',
          '@store': './src/store',
          '@utils': './src/utils',
          '@hooks': './src/hooks',
          '@types': './src/types',
          '@assets': './src/assets',
          '@config': './src/config',
          '@fullstack-monolith/api-client': '../../packages/api-client/src',
          '@fullstack-monolith/types': '../../packages/types/typescript',
        },
      },
    ],
    'react-native-reanimated/plugin',
  ],
};