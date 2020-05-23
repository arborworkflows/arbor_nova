<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Explore Cultivar Measurements</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-select 
		label="Select the Season to Model" 
		v-model="selectedSeason" 
		:items="seasons" 
		@change="loadCultivars"
		/>
          </v-flex>

	  <v-spacer></v-spacer>
 	
          <v-flex xs12>
            <v-autocomplete label="Selected Cultivar to Display" v-model="selectedCultivar" :items="cultivars" multiple />
          </v-flex>

 	<v-flex xs12 sm6>
        	<v-select
          	v-model="selectedTraits"
          	:items=allTraits
          	label="Select"
          	multiple
          	hint="Pick traits (5 or less)"
          persistent-hint
        ></v-select>
      </v-flex>

          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToRun }"
              :flat="readyToRunModel"
              :outline="!readyToRunModel"
              :disabled="!readyToRunModel"
              @click="runModel" >
              Display 
            </v-btn>
          </v-flex>
        </v-container>

	<v-spacer></v-spacer>

       </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b>Compare cultivar measurements.</b> Select a season and one or more cultivars to show the correlation plots between the cultivar's measurements 
		  during the season.  A separate selector allows you to pick which features (up to 4 or 5 simulateneously) that you want to compare. Once you have selected the season, cultivar(s), and feature(s), select the DISPLAY button to draw the plots.    
              <br></br>
		  If two traits are "correlated" with each other, the marks in the plot will tend to make a pattern
		  of dots leading up and to the right. If the traits vary inversely, the plotted points will travel down towards the
		  right.  If the dots appear random, then the two traits in this plot are not strongly related.  
              <br></br>
            </v-card-text>
          </v-card>
	  <v-row  align="center" justify="center">
	     <div id="visM" ref="visModel"></div>
	  </v-row>
        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
      </v-layout>
      </v-layout>
  </v-app>
</template>

<script>
import { utils } from '@girder/components/src';
import { Authentication as GirderAuth } from "@girder/components/src/components";
import { csvParse } from 'd3-dsv';
import scratchFolder from '../scratchFolder';
import pollUntilJobComplete from '../pollUntilJobComplete';
import optionsToParameters from '../optionsToParameters';
import JsonDataTable from '../components/JsonDataTable';
import vegaEmbed from 'vega-embed';


export default {
  name: 'terra-trait',
  inject: ['girderRest'],
  components: {
    GirderAuth,
    JsonDataTable,
  },
  data: () => ({
    seasons: ['Season 4','Season 6','S4 Hand Measurements','S4 July Features'],
    selectedSeason: '',
    cultivars: ['PI553998','PI569264'],
    selectedCultivar: '', 
    selectedTraits: [],
    allTraits: [],
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
    readyToRunModel() {
      return (this.selectedSeason.length>0) &&
	(this.selectedTraits.length>0) &&
        (this.selectedCultivar.length>0) 
    },
  },
  methods: {


    // this method is called when the season is selected.  Its purpose is to fill the this.cultivars 
    // instance variable.  When this variable is set, the cultivar selection item in the UI is automatically
    // updated, and the user can then pick from all the cultivars in a given season.  The @onchange property on 
    // the v-autocomplete is used to invoke this method.

    async loadCultivars() {
      console.log('loading season to identify cultivars');
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultRight`,
      )).data

      const params = optionsToParameters({
        // convert the string entered for the day to a number
        season: this.selectedSeason,
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/terraSeason?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);
      let seasonData = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);
      //console.log(seasonData)

      // loop through the array and fix the range,column to be integers
      var cultivarList = []
      for(let i = 0; i < seasonData.length; i++){
        cultivarList.push(seasonData[i].cultivar)
      }
      //console.log(cultivarList)
      // set the cultivar list so the UI is updated
      this.cultivars = cultivarList 
      
      // also list all available traits so we can customize the scatterplot matrix
      this.allTraits = seasonData.columns

    },


    // Once the user has selected a season and a particular cultivar to explore and selects the display button,
    // this method is invoked.  It extracts the data for the particular cultivar for that season (using the arbor_nova
    // API) and then displays a scatterplot matrix showing a subset of the data.  A subset is chosen statically to keep
    // the scatterplot from getting too big.  It would be cooler if we let the user pick the subset of attributes via 
    // a v-select with multiple selection enabled. 

    async runModel() {
      this.errorLog = null;
      this.runningModel = true;
      console.log('running model');
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultLeft`,
      )).data
      
      const params = optionsToParameters({
        season: this.selectedSeason,
        cultivar: this.selectedCultivar,
        outnameId: outname._id, });

      // and POST the data in the REST call that invokes a girder endpoint
      //this.job = (await this.girderRest.post( `arbor_nova/terraOneCultivar?${params}`,)).data;
      this.job = (await this.girderRest.post( `arbor_nova/terraSelectedCultivars?${params}`,)).data;
      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);
      var cultivarData = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);
      console.log('selected cultiver data has returned')

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);
      console.log('model is finished');

      // loop through the data array and fix the day_offset to be integers
      for(let i = 0; i < cultivarData.length; i++){
        cultivarData[i].day_offset = Number(cultivarData[i].day_offset);
      }

      // build the spec here.  Inside the method means that the data item will be available. 
      //let traitSubset = ['canopy_height','leaf_angle_alpha','leaf_angle_beta','leaf_angle_chi','day_offset']

      // the traits to display are selected by the user
      console.log(this.selectedTraits)

      var vegaLiteSpec = {
	  "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
	  "repeat": {
	    "row": this.selectedTraits, 
	    "column": this.selectedTraits 
	  },
	  "spec": {
	    "data": {"values": cultivarData}, 
	    "mark":  {type:'circle',  tooltip: {content: "data"}}, 
	    "selection": {
	      "brush": {
	        "type": "interval",
	        "resolve": "union",
	        "on": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
	        "translate": "[mousedown[event.shiftKey], window:mouseup] > window:mousemove!",
	        "zoom": "wheel![event.shiftKey]"
	      },
	      "grid": {
	        "type": "interval",
	        "resolve": "global",
	        "bind": "scales",
	        "translate": "[mousedown[!event.shiftKey], window:mouseup] > window:mousemove!",
	        "zoom": "wheel![!event.shiftKey]"
	      }
	    },
	    "encoding": {
	      "x": {"field": {"repeat": "column"}, "type": "quantitative"},
	      "y": {
	        "field": {"repeat": "row"},
	        "type": "quantitative",
	        "axis": {"minExtent": 30}
	      },
	      "color": {
	        "condition": {
	          "selection": "brush",
	          "field": "cultivar",
	          "type": "nominal"
	        },
	        "value": "grey"
	      }
	    }
	  }
	};
	vegaEmbed(this.$refs.visModel,vegaLiteSpec);
    },


  }
}
</script>
