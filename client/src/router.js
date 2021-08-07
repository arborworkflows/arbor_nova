import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import infer_rhabdo from './apps/infer_rhabdo.vue'
import infer_wsi from './apps/infer_wsi.vue'
import myod1 from './apps/myod1.vue'
import survivability from './apps/survivability.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/myod1',
      name: 'myod1',
      component: myod1,
    },
    {
      path: '/survivability',
      name: 'survivability',
      component: survivability,
    },
    {
      path: '/infer_rhabdo',
      name: 'infer_rhabdo',
      component: infer_rhabdo,
    },
     {
      path: '/infer_wsi',
      name: 'infer_wsi',
      component: infer_wsi,
    },

  ]
})
