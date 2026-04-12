import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.lakefrontleakdrain.app',
  appName: 'Lakefront Leak & Drain',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
};

export default config;
