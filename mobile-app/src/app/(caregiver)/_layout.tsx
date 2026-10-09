import { Stack } from 'expo-router';

export default function CaregiverLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="home" />
      <Stack.Screen name="pairing" />
      <Stack.Screen name="elder-details" />
      <Stack.Screen name="alerts" />
      <Stack.Screen name="reminders" />
      <Stack.Screen name="contacts" />
      <Stack.Screen name="food" />
    </Stack>
  );
}
