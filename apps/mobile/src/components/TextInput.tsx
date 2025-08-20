import React, {useState, forwardRef} from 'react';
import {
  View,
  Text,
  TextInput as RNTextInput,
  TextInputProps as RNTextInputProps,
  StyleSheet,
  TouchableOpacity,
  Animated,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import {theme} from '@config/theme';

interface TextInputProps extends RNTextInputProps {
  label?: string;
  error?: string;
  leftIcon?: string;
  rightIcon?: string;
  onLeftIconPress?: () => void;
  onRightIconPress?: () => void;
  containerStyle?: any;
  inputStyle?: any;
  labelStyle?: any;
  errorStyle?: any;
  variant?: 'default' | 'outlined' | 'filled';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  required?: boolean;
  helperText?: string;
}

export const TextInput = forwardRef<RNTextInput, TextInputProps>(
  (
    {
      label,
      error,
      leftIcon,
      rightIcon,
      onLeftIconPress,
      onRightIconPress,
      containerStyle,
      inputStyle,
      labelStyle,
      errorStyle,
      variant = 'outlined',
      size = 'medium',
      disabled = false,
      required = false,
      helperText,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const [animatedValue] = useState(new Animated.Value(props.value ? 1 : 0));

    const handleFocus = (e: any) => {
      setIsFocused(true);
      Animated.timing(animatedValue, {
        toValue: 1,
        duration: 200,
        useNativeDriver: false,
      }).start();
      props.onFocus?.(e);
    };

    const handleBlur = (e: any) => {
      setIsFocused(false);
      if (!props.value) {
        Animated.timing(animatedValue, {
          toValue: 0,
          duration: 200,
          useNativeDriver: false,
        }).start();
      }
      props.onBlur?.(e);
    };

    const getContainerStyle = () => {
      const baseStyle = [styles.container];
      
      if (variant === 'outlined') {
        baseStyle.push(styles.outlinedContainer);
      } else if (variant === 'filled') {
        baseStyle.push(styles.filledContainer);
      }
      
      if (isFocused) {
        baseStyle.push(styles.focusedContainer);
      }
      
      if (error) {
        baseStyle.push(styles.errorContainer);
      }
      
      if (disabled) {
        baseStyle.push(styles.disabledContainer);
      }
      
      return baseStyle;
    };

    const getInputStyle = () => {
      const baseStyle = [styles.input];
      
      if (size === 'small') {
        baseStyle.push(styles.smallInput);
      } else if (size === 'large') {
        baseStyle.push(styles.largeInput);
      }
      
      if (leftIcon) {
        baseStyle.push(styles.inputWithLeftIcon);
      }
      
      if (rightIcon) {
        baseStyle.push(styles.inputWithRightIcon);
      }
      
      return baseStyle;
    };

    const getLabelStyle = () => {
      const baseStyle = [styles.label];
      
      if (isFocused || props.value) {
        baseStyle.push(styles.focusedLabel);
      }
      
      if (error) {
        baseStyle.push(styles.errorLabel);
      }
      
      return baseStyle;
    };

    const animatedLabelStyle = {
      transform: [
        {
          translateY: animatedValue.interpolate({
            inputRange: [0, 1],
            outputRange: [0, -20],
          }),
        },
        {
          scale: animatedValue.interpolate({
            inputRange: [0, 1],
            outputRange: [1, 0.8],
          }),
        },
      ],
    };

    return (
      <View style={[styles.wrapper, containerStyle]}>
        {label && variant !== 'default' && (
          <Animated.View style={[styles.labelContainer, animatedLabelStyle]}>
            <Text style={[getLabelStyle(), labelStyle]}>
              {label}
              {required && <Text style={styles.required}> *</Text>}
            </Text>
          </Animated.View>
        )}
        
        {label && variant === 'default' && (
          <Text style={[styles.staticLabel, labelStyle]}>
            {label}
            {required && <Text style={styles.required}> *</Text>}
          </Text>
        )}

        <View style={getContainerStyle()}>
          {leftIcon && (
            <TouchableOpacity
              style={styles.leftIconContainer}
              onPress={onLeftIconPress}
              disabled={!onLeftIconPress}>
              <Icon
                name={leftIcon}
                size={24}
                color={
                  error
                    ? theme.colors.error
                    : isFocused
                    ? theme.colors.primary
                    : theme.colors.textSecondary
                }
              />
            </TouchableOpacity>
          )}

          <RNTextInput
            ref={ref}
            style={[getInputStyle(), inputStyle]}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholderTextColor={theme.colors.placeholder}
            editable={!disabled}
            {...props}
          />

          {rightIcon && (
            <TouchableOpacity
              style={styles.rightIconContainer}
              onPress={onRightIconPress}
              disabled={!onRightIconPress}>
              <Icon
                name={rightIcon}
                size={24}
                color={
                  error
                    ? theme.colors.error
                    : isFocused
                    ? theme.colors.primary
                    : theme.colors.textSecondary
                }
              />
            </TouchableOpacity>
          )}
        </View>

        {(error || helperText) && (
          <Text style={[error ? styles.errorText : styles.helperText, errorStyle]}>
            {error || helperText}
          </Text>
        )}
      </View>
    );
  }
);

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: theme.spacing.md,
  },
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: theme.borderRadius.md,
    backgroundColor: theme.colors.surface,
  },
  outlinedContainer: {
    borderWidth: 1,
    borderColor: theme.colors.border,
  },
  filledContainer: {
    backgroundColor: theme.colors.disabled,
  },
  focusedContainer: {
    borderColor: theme.colors.primary,
    borderWidth: 2,
  },
  errorContainer: {
    borderColor: theme.colors.error,
  },
  disabledContainer: {
    backgroundColor: theme.colors.disabled,
    opacity: 0.6,
  },
  input: {
    flex: 1,
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.md,
    fontSize: 16,
    color: theme.colors.text,
    ...theme.typography.body1,
  },
  smallInput: {
    paddingVertical: theme.spacing.sm,
    fontSize: 14,
  },
  largeInput: {
    paddingVertical: theme.spacing.lg,
    fontSize: 18,
  },
  inputWithLeftIcon: {
    paddingLeft: theme.spacing.xs,
  },
  inputWithRightIcon: {
    paddingRight: theme.spacing.xs,
  },
  labelContainer: {
    position: 'absolute',
    left: theme.spacing.md,
    zIndex: 1,
    backgroundColor: theme.colors.background,
    paddingHorizontal: theme.spacing.xs,
  },
  label: {
    fontSize: 16,
    color: theme.colors.textSecondary,
    ...theme.typography.body2,
  },
  focusedLabel: {
    color: theme.colors.primary,
    fontSize: 12,
  },
  errorLabel: {
    color: theme.colors.error,
  },
  staticLabel: {
    fontSize: 14,
    color: theme.colors.text,
    marginBottom: theme.spacing.xs,
    fontWeight: '500',
  },
  required: {
    color: theme.colors.error,
  },
  leftIconContainer: {
    paddingLeft: theme.spacing.md,
    paddingRight: theme.spacing.xs,
  },
  rightIconContainer: {
    paddingRight: theme.spacing.md,
    paddingLeft: theme.spacing.xs,
  },
  errorText: {
    fontSize: 12,
    color: theme.colors.error,
    marginTop: theme.spacing.xs,
    marginLeft: theme.spacing.md,
  },
  helperText: {
    fontSize: 12,
    color: theme.colors.textSecondary,
    marginTop: theme.spacing.xs,
    marginLeft: theme.spacing.md,
  },
});