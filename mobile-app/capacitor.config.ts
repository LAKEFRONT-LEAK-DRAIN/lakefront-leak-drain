import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.lakefrontleakdrain.app',
  appName: 'Lakefront Leak & Drain',
  webDir: 'dist',
  server: {
    url: 'https://lakefront-mobile-app.netlify.app',
    cleartext: false,
  },
};

export default config;
