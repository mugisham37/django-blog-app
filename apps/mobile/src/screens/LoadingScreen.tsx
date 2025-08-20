import React from 'react';
import {View, StyleSheet} from 'react-native';
import {ActivityIndicator, Text} from 'react-native-paper';
import LottieView from 'lottie-react-native';
import {theme} from '@config/theme';
import {useLoading} from '@store/LoadingContext';

export const LoadingScreen: React.FC = () => {
  const {loadingMessage} = useLoading();

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        {/* Lottie animation for better UX */}
        <LottieView
          source={require('../../assets/animations/loading.json')}
          autoPlay
          loop
          style={styles.animation}
        />
        
        <ActivityIndicator
          size="large"
          color={theme.colors.primary}
          style={styles.spinner}
        />
        
        <Text style={styles.message}>{loadingMessage}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  animation: {
    width: 200,
    height: 200,
    marginBottom: 20,
  },
  spinner: {
    marginBottom: 20,
  },
  message: {
    fontSize: 16,
    color: theme.colors.onBackground,
    textAlign: 'center',
    marginHorizontal: 40,
  },
});