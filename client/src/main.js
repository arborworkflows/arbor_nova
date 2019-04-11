import Vue from 'vue'
import App from './App.vue'
import GirderProvider from '@/plugins/girder';

new Vue({
  provide: GirderProvider,
  render: h => h(App),
}).$mount('#app')

Vue.config.productionTip = false
