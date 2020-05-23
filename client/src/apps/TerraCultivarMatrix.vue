<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Compare Cultivars</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-select label="Select the Season to Model" v-model="selectedSeason" :items="seasons" />
          </v-flex>

	  <v-spacer></v-spacer>

        </v-container>

	<v-spacer></v-spacer>

        <v-container fluid>
          <v-flex xs12>
	    <label for="count">How many randomly selected cultivars: </label>
	   <div id="countDiv">
              <input type="text" v-model="selectedCultivarCount">
	   </div>
          </v-flex>
        </v-container>
 	

        <v-container fluid>
          <v-flex xs12>
            <v-select label="Selected Trait to Display" v-model="selectedTrait" :items="traits" />
          </v-flex>
          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToRunRight }"
              :flat="readyToRunRight"
              :outline="!readyToRunRight"
              :disabled="!readyToRunRight"
              @click="runRight" >
              Draw Scatterplot 
            </v-btn>
          </v-flex>
        </v-container>

      </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b>Compare Cultivars</b> 
              <br><br>
		Inspiring descriptive text here.
              <br><br>
            </v-card-text>
          </v-card>
	  <v-row  align="center" justify="center">
	     <div id="visM" ref="visLeft"></div>
	     <v-column>
	       <div id="visRgt" ref="visRight"></div>
	       <div id="visRgtB" ref="visRightBelow"></div>
	     </v-column>
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
    seasons: ['Season 4','Season 6'],
    selectedSeason: '',
    selectedSeasonData: [],
    selectedCultivarCount: '',
    selectedTrait: '',
    selectedTraitColor: '',
    job: { status: 0 },
    running: false,
    runningModel: false,
    modelCompleted: false,
    traits: ["canopy_height","leaf_angle_mean","leaf_angle_alpha","leaf_angle_beta","leaf_angle_chi","per_cultivar_gboost","abserror_per_cultivar_gboost","avg_error_per_cultivar_gboost"],
    resultLeft: [],
    resultRight: [],
    resultColumnsLeft: [],
    resultColumnsRight: [],
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRunRight() {
      return (this.selectedSeason.length>0) &&
        (this.selectedCultivarCount.length>0) &&
        (this.selectedTrait.length>0); 
    },
  },

  methods: {

    // do a REST call to get the measurements from the selected season
    async renderCultivar1Data(globalthis,cultivar) {
      const outname = (await globalthis.girderRest.post( `item?folderId=${globalthis.scratchFolder._id}&name=selectedSeasonData`,)).data
      const params = optionsToParameters({
        season: globalthis.selectedSeason,
	cultivar: cultivar,
        outnameId: outname._id, });
      // and POST the data in the REST call that invokes a girder endpoint
      globalthis.job = (await globalthis.girderRest.post( `arbor_nova/terraOneCultivar?${params}`,)).data;
      await pollUntilJobComplete(globalthis.girderRest, globalthis.job, job => globalthis.job = job);
      var cultivarData = csvParse((await globalthis.girderRest.get(`item/${outname._id}/download`)).data);
      console.log('selected cultiver data has returned')


      // loop through the data array and fix the day_offset to be integers
      for(let i = 0; i < cultivarData.length; i++){ 
        cultivarData[i].day_offset = Number(cultivarData[i].day_offset);
      } 


      // render
      var cult1Title = "values of "+globalthis.selectedTrait + " for  cultivar "+ cultivar
      var cult1spec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v4.8.1.json',
     	description: 'trait values across the field',
      	title: cult1Title,
      	width: 300,
       	height: 350,
       	data: {values: cultivarData},
       	mark: {type:'point', tooltip: {content: "data"}},
       	encoding: {
            color: {field: globalthis.selectedTrait, type: 'quantitative'},
       	    x: {field: 'day_offset', type: 'ordinal'},
       	    y: {field: globalthis.selectedTrait, type: 'quantitative'},
	}
      };
      // Draw the values of the selected trait for all the measurements during the season
      // on this cultivar only
      console.log('got here')
      vegaEmbed(globalthis.$refs.visRight,cult1spec);
    },


    // do a REST call to get the measurements from the selected season
    async renderCultivar2Data(globalthis,cultivar) {
      const outname = (await globalthis.girderRest.post( `item?folderId=${globalthis.scratchFolder._id}&name=selectedSeasonData`,)).data
      const params = optionsToParameters({
        season: globalthis.selectedSeason,
	cultivar: cultivar,
        outnameId: outname._id, });
      // and POST the data in the REST call that invokes a girder endpoint
      globalthis.job = (await globalthis.girderRest.post( `arbor_nova/terraOneCultivar?${params}`,)).data;
      await pollUntilJobComplete(globalthis.girderRest, globalthis.job, job => globalthis.job = job);
      var cultivarData = csvParse((await globalthis.girderRest.get(`item/${outname._id}/download`)).data);
      console.log('selected cultiver data has returned')

      // loop through the data array and fix the day_offset to be integers
      for(let i = 0; i < cultivarData.length; i++){ 
        cultivarData[i].day_offset = Number(cultivarData[i].day_offset);
      } 

      // render
      var cult1Title = "values of "+globalthis.selectedTrait + " for  cultivar "+ cultivar
      var cult1spec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v4.8.1.json',
     	description: 'trait values across the field',
      	title: cult1Title,
      	width: 300,
       	height: 350,
       	data: {values: cultivarData},
       	mark: {type:'point', tooltip: {content: "data"}},
       	encoding: {
            color: {field: globalthis.selectedTrait, type: 'quantitative'},
       	    x: {field: 'day_offset', type: 'ordinal'},
       	    y: {field: globalthis.selectedTrait, type: 'quantitative'},
	}
      };
      // Draw the values of the selected trait for all the measurements during the season
      // on this cultivar only
      console.log('got here #2')
      vegaEmbed(globalthis.$refs.visRightBelow,cult1spec);
    },



    // this is called when the cultivar matrix is desired.  A Vega-Lite spec is used for the rendering.
    // The data for the rendering is retrieved from a girder REST endpoint 

    async runRight() {
      this.running = true;
      this.errorLog = null;
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultRight`,
      )).data

      // fill the parameters needed to invoke the python REST endpoint 
      const params = optionsToParameters({
        // convert the string entered for the day to a number
        season: this.selectedSeason,
	count: Number(this.selectedCultivarCount),
	trait: this.selectedTrait,
        outnameId: outname._id,
      });

      // and POST the data in the REST call that invokes a girder endpoint
      this.job = (await this.girderRest.post(
        `arbor_nova/terraCultivarMatrix?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.resultRight = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);

      // build the spec here.  Inside the method means that the data item will be available.   This is more complicated
      // than a usual spec because it allows selection of a single square and then "projects" the fields of 
      // 'cultivar1','cultivar2', and 'difference' so that an event listener will receive all fields of the clicked
      // object.  This enables a secondary visualization, depending on what the user clicked on the master matrix.

      var thisTitle = "Comparing "+this.selectedTrait + " across Cultivars"
      var vegaLiteSpec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v4.8.1.json',
        description: 'trait values across the field',
	title: thisTitle, 
	width: 800,
	height: 800,
        data: {values: this.resultRight}, 
        mark: {type:'rect', strokeWidth: 1, tooltip: {content: "data"}},
	selection: {
    	    "highlight": {"type": "single", "empty": "none", "on": "mouseover"},
    	    "select": {"type": "single", fields:['cultivar1','cultivar2','difference']}
  	},
        encoding: {
          color: {field: "difference", type: 'quantitative'},
          x: {field: "cultivar2", type: 'ordinal'},
          y: {field: "cultivar1", type: 'ordinal'},
          stroke: {
             "condition": {"test": {"and": [{"selection": "select"}, "length(data(\"select_store\"))"]}, "value": "black"},
      "value": null
         },
	 fillOpacity: {
            condition: {"selection": "select", "value": 1},
            value: 0.5
         },
        }
      };
	// here is the embedding of the Vega-lite viz.  Note the promise-catching "then" clause, which adds a listener
	// to the selection event.  The convention of eventname_store is used to store/retrieve data managed by vega.
	// 
        console.log('before the embed #1. this:',this)
	var globalThis = this
	
	vegaEmbed(this.$refs.visLeft,vegaLiteSpec).then(function(result) {
		result.view.addSignalListener('select',function(name,value) { 
			console.log('value:',value); 
      		// now we know what was selected, get the data for these cultivars and render 
      		globalThis.renderCultivar1Data(globalThis,value.cultivar1[0]).then(function() {
      		    globalThis.renderCultivar2Data(globalThis,value.cultivar2[0]);
      		console.log('selected cultiver data has returned')});
	  });
      });
    }
      if (this.job.status === 4) {
        this.running = false;
      }
  },

 }
}
</script>
