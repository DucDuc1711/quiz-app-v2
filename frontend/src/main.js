import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

import './assets/main.css'
import '@fontsource/noto-sans/vietnamese.css'

import App from './App.vue'
import router from './router'

import './api/axios'

const app = createApp(App)
app.use(createPinia())
app.use(router)

app.mount('#app')
