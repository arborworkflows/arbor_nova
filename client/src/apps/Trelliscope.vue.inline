<template>
  <div id="htmlwidget-f690905e5c2003a50cdf" style="width:100%;height:100%;" class="trelliscopejs_widget html-widget"></div>
</template>

<script 
	type="application/json" 
	data-for="htmlwidget-f690905e5c2003a50cdf">{"x":{"id":"370d2f4e","config_info":"'appfiles/config.jsonp'","self_contained":false,"latest_display":{"name":"By_position","group":"common"},"spa":true,"in_knitr":false,"in_shiny":false,"in_notebook":false},"evals":[],"jsHooks":[]}
</script>

<script>

import { utils } from '@girder/components/src';
import { Authentication as GirderAuth } from "@girder/components/src/components";
import { csvParse } from 'd3-dsv';
import scratchFolder from '../scratchFolder';
import pollUntilJobComplete from '../pollUntilJobComplete';
import optionsToParameters from '../optionsToParameters';


export default {
  name: 'trelliscope',
  inject: ['girderRest'],
  components: {
    GirderAuth,
  },

  created() {
    //let htmlwidgets = document.createElement('script');    
    //htmlwidgets.setAttribute('src','lib/htmlwidgets-1.5.1/htmlwidgets.js');
    //document.head.appendChild(htmlwidgets);
    //let trelliscopeCode = document.createElement('script');    
    //trelliscopeCode.setAttribute('src','lib/trelliscopejs_widget-0.3.2/trelliscope.min.js');
    //document.head.appendChild(trelliscopeCode);
    //let bindings = document.createElement('script');    
    //bindings.setAttribute('src','lib/trelliscopejs_widget-binding-0.2.7/trelliscopejs_widget.js');
    //document.head.appendChild(bindings);
  },

  data: () => ({
    seasons: ['Season 4'],
    selectedSeason: 'Season 4',
    job: { status: 0 },
    running: false,
    runningModel: false,
    modelCompleted: false,
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRunRight() {
      return (this.selectedSeason.length>0) 
    },
  },

  methods: {

  },
}
</script>
