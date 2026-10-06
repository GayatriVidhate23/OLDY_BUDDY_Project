import React from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

export default function Layout() {
  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: '#3730a3' },
          headerTintColor: '#ffffff',
          headerTitleStyle: { fontSize: 22, fontWeight: 'bold' },
          headerBackTitleVisible: false,
        }}
      >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="login" options={{ title: 'Oldy Buddy Sign In' }} />
        <Stack.Screen name="home" options={{ title: 'My Oldy Buddy Home' }} />
        <Stack.Screen name="reminders" options={{ title: 'My Reminders' }} />
        <Stack.Screen name="conversation" options={{ title: 'Talk to Oldy Buddy' }} />
        <Stack.Screen name="sos" options={{ title: 'Emergency SOS Help' }} />
        <Stack.Screen name="profile" options={{ title: 'My Profile' }} />
      </Stack>
    </>
  );
}
