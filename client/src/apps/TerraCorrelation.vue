<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Correlation Between Traits</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-select 
		label="Select the Season to Model" 
		v-model="selectedSeason" 
		:items="seasons" 
		/>
          </v-flex>

	  <v-spacer></v-spacer>
 	
          <v-flex xs12>
            <v-autocomplete label="Select a Correlation Method" v-model="selectedCorrelation" :items="correlations" />
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
              <b>Examine the trait correlation matrix.</b> This application reads the trait measurements from the selected season 
		and displays a pairwise correlation matrix showing how 'related' two different traits are for the measurements 
		examined in this season.  
              <br></br>
	      Please start by selecting a season to examine on the left.  Three different types of correlation algorithms are supported:
	      Pearson Correlation, Kendell Tau Correlation, and Spearman Rank Correlation. Please choose the preferred method and then
	      click the DISPLAY button to calculate and display the result.  
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
import vegaEmbed from 'vega-embed';


export default {
  name: 'terra-correlation',
  inject: ['girderRest'],
  components: {
    GirderAuth,
  },
  data: () => ({
    seasons: ['Season 4','Season 6','S4 Hand Measurements','S4 July Features'],
    selectedSeason: '',
    correlations: ['Pearson Correlation','Kendell Tau Correlation','Spearman Rank Correlation'],
    selectedCorrelation: '', 
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
	(this.selectedCorrelation.length>0) 
    },
  },
  methods: {



    // Once the user has selected a season and a particular correlation method,  
    // this method is invoked.  It extracts the data for the correlation matrix from a particular  season (using the arbor_nova
    // API) and then displays a heatmap of the matrix using Vega-lite

    async runModel() {
      this.errorLog = null;
      this.runningModel = true;
      console.log('running model');
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultLeft`,
      )).data
      
      const params = optionsToParameters({
        season: this.selectedSeason,
        correlation: this.selectedCorrelation,
        outnameId: outname._id, });

      // and POST the data in the REST call that invokes a girder endpoint
      this.job = (await this.girderRest.post( `arbor_nova/terraCorrelation?${params}`,)).data;
      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);
      var correlationData = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);
      console.log('correlation data has returned')

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);
      console.log('model is finished');


      // build the spec here.  Inside the method means that the data item will be available. 
      let titleString = this.selectedSeason+': correlation matrix using '+this.selectedCorrelation
      var vegaLiteSpec = {
	"$schema": "https://vega.github.io/schema/vega-lite/v4.json",
	title: titleString,
        width: 800,
        height: 800,
        data: {values: correlationData},
        mark: {type:'rect',  tooltip: {content: "data"}},
        encoding: {
          x: {field: 'variable2', type: 'ordinal'},
          y: {field: 'variable', type: 'ordinal'},
          color: {
                field: 'correlation', 
                type: 'quantitative',
                "scale": {"scheme":"lightmulti", "domainMid" : 0}
          }
        }

      };
      vegaEmbed(this.$refs.visModel,vegaLiteSpec);
    },


  }
}
</script>
