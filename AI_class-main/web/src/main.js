import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import store from "./stores";
import Antd from 'ant-design-vue'

import 'ant-design-vue/dist/reset.css'
import './assets/main.css'
import { createVuestic } from 'vuestic-ui'
import 'vuestic-ui/css'
import "./assets/scss/argon-dashboard.scss";

import "./assets/css/nucleo-icons.css";



const app = createApp(App)
app.use(createVuestic())
app.use(createPinia())
app.use(router)
app.use(store)
app.use(Antd)

app.mount('#app')
