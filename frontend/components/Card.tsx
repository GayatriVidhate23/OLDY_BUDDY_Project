import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ViewStyle } from 'react-native';

interface CardProps {
  title?: string;
  children?: React.ReactNode;
  style?: ViewStyle;
  onPress?: () => void;
  bgColor?: string;
}

export const Card: React.FC<CardProps> = ({ title, children, style, onPress, bgColor }) => {
  const content = (
    <View style={[styles.card, bgColor ? { backgroundColor: bgColor } : null, style]}>
      {title ? <Text style={styles.title}>{title}</Text> : null}
      {children}
    </View>
  );

  if (onPress) {
    return (
      <TouchableOpacity activeOpacity={0.85} onPress={onPress}>
        {content}
      </TouchableOpacity>
    );
  }

  return content;
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 20,
    padding: 22,
    marginVertical: 10,
    marginHorizontal: 16,
    borderWidth: 2,
    borderColor: '#cbd5e1',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0f172a',
    marginBottom: 8,
  },
});
