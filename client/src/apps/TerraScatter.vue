<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Pairwise Trait Explorer</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-select 
		label="Select the Season to Model" 
		v-model="selectedSeason" :items="seasons"
                @change="loadSeasonColumns" />
          </v-flex>

	  <v-spacer></v-spacer>

        </v-container>

	<v-spacer></v-spacer>

        <v-container fluid>
          <v-flex xs12>
            <v-select label="Selected Trait to Display on Vertical Axis" v-model="selectedTraitLeft" :items="traits" />
          </v-flex>
        </v-container>
 	
        <v-container fluid>
          <v-flex xs12>
            <v-select label="Selected Trait to Display on Horizontal Axis" v-model="selectedTraitRight" :items="traits" />
          </v-flex>
	  <v-spacer></v-spacer>
          <v-flex xs12>
            <v-select label="Selected Trait to use for color" v-model="selectedTraitColor" :items="traits" />
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
              <b>Compare the correlation between two traits.</b>
              <br><br>
		This app plots the values of two selected traits for each measurement during a season.  The purpose is to
		look for any correlations. A positive correlation is indicated  by a trend  points going up and right within the chart.  
		An inverse correlation would produce a trend of points leading down and right within the chart.  
              <br></br>
		NOTE: this rendering technique currently only works to compare two continuous traits.  If either trait selected is
		categorical in value, the plot will be blank.  Please select traits with numeric values instead. 
            </v-card-text>
          </v-card>
	  <v-row  align="center" justify="center">
	     <div id="visM" ref="visRight"></div>
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
    seasonData: [],
    selectedTraitLeft: '',
    selectedTraitRight: '',
    selectedTraitColor: '',
    traits: [],
    job: { status: 0 },
    running: false,
    runningModel: false,
    modelCompleted: false,
    resultLeft: [],
    resultRight: [],
    resultModel: [],
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
        (this.selectedTraitLeft.length>0) &&
        (this.selectedTraitColor.length>0) &&
        (this.selectedTraitRight.length>0); 
    },
  },

  methods: {



   async loadSeasonColumns() {
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
       var columnList = seasonData.columns
       //console.log(columnList)
       
       // remove 'cultivar' from list if it is there. We only want to return numberic measurements for the
       // traits for use in scatter plots or other visualizations.
       
       const index = columnList.indexOf('cultivar');
       if (index > -1) {
         columnList.splice(index, 1);
       }

       // list all available traits so we can customize the scatterplot matrix
       this.traits = columnList
     },




    // this is called when the right field display is desired.  A Vega-Lite spec is used for the rendering.
    // The data for the rendering is retrieved from a girder REST endpoint 

    async runRight() {
      this.running = true;
      this.errorLog = null;
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

      if (this.job.status === 3) {
        this.running = false;
        this.resultRight = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);

     // loop through the array and fix the range,column to be integers
      for(let i = 0; i < this.resultRight.length; i++){
        this.resultRight[i].range = Number(this.resultRight[i].range);
        this.resultRight[i].column = Number(this.resultRight[i].column);
      }

      // build the spec here.  Inside the method means that the data item will be available.   A 'selection'
      // object is added to the spec allow zoom & pan of the scatterplot on desktop systems. 

      var vegaLiteSpec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v4.8.1.json',
        description: 'trait values across the field',
	title: 'Correlation between '+this.selectedTraitRight+' and '+this.selectedTraitLeft,
	width: 800,
	height: 800,
        data: {values: this.resultRight}, 
 	"selection": {
	    "grid": {
	    "type": "interval", "bind": "scales"
    	    }
  	},
        mark: {type:'point', fill: "#4C78A8", tooltip: {content: "data"}},
        encoding: {
          x: {field: this.selectedTraitRight, type: 'quantitative'},
          y: {field: this.selectedTraitLeft, type: 'quantitative'},
          color: {
		field: this.selectedTraitColor , 
		type: 'quantitative',
		"scale": {"scheme":"lightmulti"}
	  }
        }
      };
	vegaEmbed(this.$refs.visRight,vegaLiteSpec);
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },
  }
}
</script>
