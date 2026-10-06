import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';

const Colors = { 
  primary: '#0ea5e9', // Sky blue
  danger: '#111827',  // Dark UI for danger (or keep red?) Let's use dark for SOS per SaaS design, but danger might need red. We'll use red for true danger, and dark for primary action.
  dark: '#111827',
  lime: '#ccff00',
  red: '#ef4444'
};

export const LargeButton = ({ title, onPress, variant = 'primary' }: any) => {
  const bgColor = (Colors as any)[variant] || Colors.primary;
  const textColor = variant === 'lime' ? '#111827' : '#ffffff';
  
  return (
    <TouchableOpacity style={[styles.button, { backgroundColor: bgColor }]} onPress={onPress}>
      <Text style={[styles.text, { color: textColor }]}>{title}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: { 
    paddingVertical: 24, 
    paddingHorizontal: 32, 
    borderRadius: 24, 
    marginVertical: 12, 
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3
  },
  text: { 
    fontSize: 24, 
    fontWeight: '700' 
  }
});
