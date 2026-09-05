import {defineConfig,devices} from '@playwright/test';
export default defineConfig({testDir:'./e2e',fullyParallel:true,retries:2,use:{baseURL:'http://127.0.0.1:3004',trace:'retain-on-failure'},webServer:{command:'npm run dev',url:'http://127.0.0.1:3004',reuseExistingServer:!process.env.CI,timeout:120000},projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}]});
