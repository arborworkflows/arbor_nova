<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Top-K Ranking</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>

          <v-flex xs12>
            <v-select label="Select the Season to Model" v-model="selectedSeason" :items="seasons" />
          </v-flex>

  	  <v-subheader class="pl-0">How many rankings to show?</v-subheader>
          <v-slider
            v-model="topKslider"
	    min=5
	    max=50
            thumb-label="always" >
	  </v-slider>

          <v-flex xs12>
	    <label for="sDay">Enter the day in the season</label>
	   <div id="dayDiv">
              <input type="text" v-model="selectedDayLeft">
	   </div>
          </v-flex>
          <v-flex xs12>
            <v-select label="Selected Trait to Display" v-model="selectedTraitLeft" :items="traits" />
          </v-flex>
          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToRun }"
              :flat="readyToRunLeft"
              :outline="!readyToRunLeft"
              :disabled="!readyToRunLeft"
              @click="runLeft" >
              Draw Left Chart
            </v-btn>
          </v-flex>
        </v-container>
 	
	<v-spacer></v-spacer>

        <v-container fluid>
          <v-flex xs12>
	    <label for="sDayRight">Enter the day in the season</label>
	   <div id="dayDivRight">
              <input type="text" v-model="selectedDayRight">
	   </div>
          </v-flex>
          <v-flex xs12>
            <v-select label="Selected Trait to Display" v-model="selectedTraitRight" :items="traits" />
          </v-flex>
          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToRun }"
              :flat="readyToRunRight"
              :outline="!readyToRunRight"
              :disabled="!readyToRunRight"
              @click="runRight" >
              Draw Right Chart
            </v-btn>
          </v-flex>
        </v-container>

      </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b>Rank the cultivars.</b> Select a day within the growing season
		and pick a trait from the selectors at the left.   Then select GO to explore how the cultivars 
		compared on that selected trait at that time during the season.
              <br><br>
            </v-card-text>
          </v-card>
	  <v-row  align="center" justify="center">
	     <div id="vis" ref="visLeft"></div>
	     <div id="vis" ref="visRight"></div>
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
    topKslider: 10,
    selectedDayLeft: "15",
    selectedDayRight: "15",
    selectedTraitLeft: '',
    selectedTraitRight: '',
    job: { status: 0 },
    running: false,
    traits: ["canopy_height","leaf_angle_mean","leaf_angle_alpha","leaf_angle_beta","leaf_angle_chi","single_xgboost","abserror_single_xgboost","single_dtree","abserror_single_dtree"],
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
    readyToRunLeft() {
      return !!(this.selectedDayLeft>0) &&
        !!(this.selectedTraitLeft.length>0); 
    },
    readyToRunRight() {
      return !!(this.selectedDayRight>0) &&
        !!(this.selectedTraitRight.length>0); 
    },
    loggedOut() {
      return this.girderRest.user === null;
    },
  },
  methods: {
    async runLeft() {
      this.running = true;
      this.errorLog = null;
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultLeft`,
      )).data

      const params = optionsToParameters({
	// convert the string entered for the day to a number
	season: this.selectedSeason,
        selectedDay: Number(this.selectedDayLeft),
        selectedTrait: this.selectedTraitLeft,
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/terraTraitDaily?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.resultLeft = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);

      // loop through the array and fix the range,column to be integers
      for(let i = 0; i < this.resultLeft.length; i++){ 
	this.resultLeft[i].range = Number(this.resultLeft[i].range);
	this.resultLeft[i].column = Number(this.resultLeft[i].column);
      }

     // we need to dynamically create a data column, so build the name according to 
     // the trait we will be visualization

     var aggTraitName = 'aggregate_'+this.selectedTraitLeft;
     var titleText = 'Ranking '+ this.selectedSeason+': cultivars ranked by '+this.selectedTraitLeft+' on day ' +this.selectedDayLeft
     var sliderValue = this.topKslider;
     var vegaLiteSpec = {

        "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
	"title": titleText,
        "data": {"values": this.resultLeft}, 
        "width": 477,
        "height": 477,
        "mark": {"type": "bar", "tooltip": null},
        "transform": [
          {
            "aggregate": [
              {"op": "mean", "field": this.selectedTraitLeft, "as": aggTraitName}
            ],
            "groupby": ["cultivar"]
          },
          {
            "window": [{"op": "row_number", "as": "rank"}],
            "sort": [{"field": aggTraitName, "order": "descending"}]
          },
          {
            "calculate": "datum.rank < 20 ? datum.cultivar : 'All Others'",
            "as": "ranked_cultivar"
          }
        ],
        "encoding": {
          "x": {
            "aggregate": "mean",
            "field": aggTraitName,
            "type": "quantitative",
            "axis": {"title": null}
          },
          "y": {
            "sort": {"op": "mean", "field": aggTraitName, "order": "descending"},
            "field": "ranked_cultivar",
            "type": "ordinal",
            "axis": {"title": null}
          }
        }
      };

	vegaEmbed(this.$refs.visLeft,vegaLiteSpec);
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },

    async runRight() {
      this.running = true;
      this.errorLog = null;
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultRight`,
      )).data

      const params = optionsToParameters({
	// convert the string entered for the day to a number
	season: this.selectedSeason,
        selectedDay: Number(this.selectedDayRight),
        selectedTrait: this.selectedTraitRight,
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/terraTraitDaily?${params}`,
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

      // build the spec here.  Inside the method means that the data item will be available. 
      var titleText = 'Ranking '+ this.selectedSeason+': cultivars ranked by '+this.selectedTraitRight+' on day ' +this.selectedDayRight
      var aggTraitName = 'agg_'+this.selectedTraitRight;
      var sliderValue = this.topKslider;
      let globalThis = this;
      var vegaLiteSpec = {
        "$schema": "https://vega.github.io/schema/vega-lite/v3.json",
	"title": titleText,
        "data": {"values": this.resultRight}, 
        "width": 477,
        "height": 477,
        "mark": {"type": "bar", "tooltip": null},
        "transform": [
          {
            "aggregate": [
              {"op": "mean", "field": this.selectedTraitRight, "as": aggTraitName}
            ],
            "groupby": ["cultivar"]
          },
          {
            "window": [{"op": "row_number", "as": "rank"}],
            "sort": [{"field": aggTraitName, "order": "descending"}]
          },
          {
            "calculate": "datum.rank < 20 ? datum.cultivar : 'All Others'",
            "as": "ranked_cultivar"
          }
        ],
        "encoding": {
          "x": {
            "aggregate": "mean",
            "field": aggTraitName,
            "type": "quantitative",
            "axis": {"title": null}
          },
          "y": {
            "sort": {"op": "mean", "field": aggTraitName, "order": "descending"},
            "field": "ranked_cultivar",
            "type": "ordinal",
            "axis": {"title": null}
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
