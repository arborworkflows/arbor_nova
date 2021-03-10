import Vue from 'vue'
import Router from 'vue-router'
import Home from './views/Home.vue'
import AppendColumn from './apps/AppendColumn.vue'
import PGLS from './apps/PGLS.vue'
//import PhyloMap from './apps/PhyloMap.vue'
import ASR from './apps/ASR.vue'
import PolyA from './apps/PolyA.vue'
import blastn from './apps/blastn.vue'
import infer from './apps/infer.vue'
import DockerPolyA from './apps/DockerPolyA.vue'
import infer_rhabdo from './apps/infer_rhabdo.vue'
import infer_wsi from './apps/infer_wsi.vue'
import tp53_mutation from './apps/tp53_mutation.vue'
import tmia_classification from './apps/tmia_classification.vue'

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
      path: '/polya',
      name: 'polya',
      component: PolyA,
    },
    {
      path: '/docker_polya',
      name: 'docker_polya',
      component: DockerPolyA,
    },
    {
      path: '/blastn',
      name: 'blastn',
      component: blastn,
    },
    {
      path: '/infer',
      name: 'infer',
      component: infer,
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
    {
      path: '/tp53_mutation',
      name: 'tp53_mutation',
      component: tp53_mutation,
    }, 
    {
      path: '/tmia_classification',
      name: 'tmia_classification',
      component: tmia_classification,
    },

  ]
})
