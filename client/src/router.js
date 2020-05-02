import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import AppendColumn from './apps/AppendColumn.vue'
import PGLS from './apps/PGLS.vue'
import TerraTrait from './apps/TerraTrait.vue'
import TerraModel from './apps/TerraModel.vue'
//import PhyloMap from './apps/PhyloMap.vue'
import ASR from './apps/ASR.vue'

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
      path: '/terratrait',
      name: 'terratrait',
      component: TerraTrait,
    },
    {
      path: '/terramodel',
      name: 'terramodel',
      component: TerraModel,
    },
//    {
//      path: '/pgls',
//      name: 'pgls',
//      component: PGLS,
//    },
//    {
//      path: '/phylomap',
//      name: 'phylomap',
//      component: PhyloMap,
//    },
//    {
//      path: '/asr',
//      name: 'asr',
//      component: ASR,
//    },
  ]
})
