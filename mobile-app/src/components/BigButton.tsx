import { TouchableOpacity, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';
import { theme } from '../theme';

interface BigButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  style?: ViewStyle;
  textStyle?: TextStyle;
  disabled?: boolean;
}

export function BigButton({ title, onPress, variant = 'primary', style, textStyle, disabled }: BigButtonProps) {
  let backgroundColor: string = theme.colors.primary;
  let color: string = theme.colors.background;

  if (variant === 'secondary') {
    backgroundColor = theme.colors.surface;
    color = theme.colors.text;
  } else if (variant === 'danger') {
    backgroundColor = theme.colors.error;
    color = theme.colors.background;
  }

  if (disabled) {
    backgroundColor = theme.colors.border;
    color = theme.colors.textSecondary;
  }

  return (
    <TouchableOpacity
      style={[styles.button, { backgroundColor }, style]}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.7}
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={title}
    >
      <Text style={[styles.text, { color }, textStyle]} allowFontScaling={true}>
        {title}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 72,
    borderRadius: theme.roundness,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.xl,
    paddingVertical: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  text: {
    ...theme.typography.button,
    textAlign: 'center',
  },
});
