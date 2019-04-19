import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import AppendColumn from './apps/AppendColumn.vue'
import PGLS from './apps/PGLS.vue'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/appendcolumn',
      name: 'appendcolumn',
      component: AppendColumn,
    },
    {
      path: '/pgls',
      name: 'pgls',
      component: PGLS,
    },
  ]
})
