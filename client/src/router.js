import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import AppendColumn from './apps/AppendColumn.vue'
import PGLS from './apps/PGLS.vue'
//import PhyloMap from './apps/PhyloMap.vue'
import ASR from './apps/ASR.vue'
import PolyA from './apps/PolyA.vue'
import PhyloSignal from './apps/PhyloSignal.vue'
import FitDiscrete from './apps/FitDiscrete.vue'
import FitContinuous from './apps/FitContinuous.vue'
import PIC from './apps/PIC.vue'

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
//    {
//      path: '/phylomap',
//      name: 'phylomap',
//      component: PhyloMap,
//    },
    {
      path: '/asr',
      name: 'asr',
      component: ASR,
    },
    {
      path: '/phylosignal',
      name: 'phylosignal',
      component: PhyloSignal,
    },
    {
      path: '/fitdiscrete',
      name: 'fitdiscrete',
      component: FitDiscrete, 
    },
    {
      path: '/fitcontinuous',
      name: 'fitcontinuous',
      component: FitContinuous,
    },
    {
      path: '/pic',
      name: 'pic',
      component: PIC,
    },
  ]
})
