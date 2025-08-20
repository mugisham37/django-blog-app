import React from 'react';
import {View, StyleSheet, Dimensions} from 'react-native';
import {Text, Button} from 'react-native-paper';
import {SafeAreaView} from 'react-native-safe-area-context';
import {StackNavigationProp} from '@react-navigation/stack';
import LottieView from 'lottie-react-native';
import {OnboardingStackParamList} from '@navigation/OnboardingNavigator';
import {useOnboarding} from '@hooks/useOnboarding';
import {theme} from '@config/theme';

const {width, height} = Dimensions.get('window');

type OnboardingCompleteScreenNavigationProp = StackNavigationProp<
  OnboardingStackParamList,
  'OnboardingComplete'
>;

interface Props {
  navigation: OnboardingCompleteScreenNavigationProp;
}

export const OnboardingCompleteScreen: React.FC<Props> = ({navigation}) => {
  const {completeOnboarding} = useOnboarding();

  const handleGetStarted = async () => {
    await completeOnboarding();
    // Navigation will be handled automatically by AppNavigator
    // when onboarding is completed
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.animationContainer}>
          <LottieView
            source={require('../../../assets/animations/success.json')}
            autoPlay
            loop={false}
            style={styles.animation}
          />
        </View>

        <View style={styles.textContainer}>
          <Text style={styles.title}>You're All Set!</Text>
          <Text style={styles.subtitle}>
            Welcome to Fullstack Monolith! You're ready to start creating, sharing, and connecting with your community.
          </Text>
        </View>

        <View style={styles.featuresContainer}>
          <View style={styles.feature}>
            <Text style={styles.featureIcon}>🎉</Text>
            <Text style={styles.featureText}>Setup completed successfully</Text>
          </View>
          <View style={styles.feature}>
            <Text style={styles.featureIcon}>🔐</Text>
            <Text style={styles.featureText}>Your account is secure</Text>
          </View>
          <View style={styles.feature}>
            <Text style={styles.featureIcon}>📱</Text>
            <Text style={styles.featureText}>Mobile app is ready to use</Text>
          </View>
          <View style={styles.feature}>
            <Text style={styles.featureIcon}>🚀</Text>
            <Text style={styles.featureText}>Start exploring features</Text>
          </View>
        </View>

        <View style={styles.buttonContainer}>
          <Button
            mode="contained"
            onPress={handleGetStarted}
            style={styles.button}
            contentStyle={styles.buttonContent}
            labelStyle={styles.buttonLabel}>
            Start Using the App
          </Button>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
  },
  animationContainer: {
    alignItems: 'center',
    marginTop: 60,
  },
  animation: {
    width: width * 0.6,
    height: height * 0.25,
  },
  textContainer: {
    alignItems: 'center',
    marginVertical: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: theme.colors.primary,
    textAlign: 'center',
    marginBottom: 20,
  },
  subtitle: {
    fontSize: 16,
    color: theme.colors.onSurface,
    textAlign: 'center',
    lineHeight: 24,
    marginHorizontal: 20,
  },
  featuresContainer: {
    marginVertical: 20,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  featureIcon: {
    fontSize: 28,
    marginRight: 20,
  },
  featureText: {
    fontSize: 16,
    color: theme.colors.onBackground,
    flex: 1,
    fontWeight: '500',
  },
  buttonContainer: {
    paddingBottom: 40,
  },
  button: {
    borderRadius: 25,
    elevation: 4,
  },
  buttonContent: {
    paddingVertical: 12,
  },
  buttonLabel: {
    fontSize: 18,
    fontWeight: '600',
  },
});