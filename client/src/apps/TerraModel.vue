<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Trait Model Trainer</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-select label="Select the Season to Model" v-model="selectedSeason" :items="seasons" />
          </v-flex>

	  <v-spacer></v-spacer>
 	

          <v-flex xs12>
	    <label for="estimators">Number of solutions to explore (10..500)</label>
	   <div >
              <input type="text" v-model="estimators">
	   </div>
          </v-flex>
          <v-flex xs12>
	    <label >Model's decision depth to explore (1..50)</label>
	   <div >
              <input type="text" v-model="maxDepth">
	   </div>
          </v-flex>
          <v-flex xs12>
	    <label >Learning rate for the model (0.001..0.5)</label>
	   <div >
              <input type="text" v-model="learningRate">
	   </div>
          </v-flex>
          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToRun }"
              :flat="readyToRunModel"
              :outline="!readyToRunModel"
              :disabled="!readyToRunModel"
              @click="runModel" >
              Run Model 
            </v-btn>
          </v-flex>
        </v-container>

	<v-spacer></v-spacer>

        <v-container fluid>
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

        <v-container fluid>
         <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToDownload }"
              :flat="readyToDownload"
              :outline="!readyToDownload"
              :disabled="!readyToDownload"
              @click="downloadResults"
            >
              Download Model Results 
            </v-btn>
          </v-flex>

        </v-container>

      </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b>Fit a model to observed measurements.</b>This app contains an embedded XGBoost machine learning 
		model, which can be used to predict canopy_height from recorded sensor data (day-of-season, leaf measurements). 
		To train the model, frist select the season. Default values are provided for each input parameter that 
		can be used to change the model and make it more or less accurate.  Default values are provided.  Once you
		are satisfied with the model parameters, click RUN MODEL. 
		Please allow a few seconds to a few minutes for execution, depending on the model parameters.  When the model 
		is finished, it will draw the entire field showing the average error between the measurements and the model
		for each plot location across the season. 
              <br></br>
		You may change parameters and re-run the model as often as you wish. When the model is finished, 
		you may browse how the model matched during a particular day of the season using the specific day and
		 specific feature rendering tools. The controls for the selected day renderings are at left below the 
		modeling parameters.   Click on the DRAW LEFT CHART or DRAW RIGHT CHART to render a feature at the 
		selected day. 
              <br></br>
	        If you wish to save the results of the model fitting for further analysis, click on the "DOWNLOAD MODEL RESULTS"
		button to download a CSV file of the sensor measurements as well as predictions made by the newly fit model  to 
		match the measured  canopy_heights.
            </v-card-text>
          </v-card>
	  <v-row  align="center" justify="center">
	     <div id="visM" ref="visModel"></div>
	     <div id="visL" ref="visLeft"></div>
	     <div id="visR" ref="visRight"></div>
	  </v-row>
        <div v-if="runningModel" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
	  <v-progress-linear  :indeterminate="true" > </v-progress-circular>
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
    estimators: "100",
    maxDepth: "8",
    learningRate: "0.1",
    selectedDayLeft: "15",
    selectedDayRight: "15",
    selectedTraitLeft: '',
    selectedTraitRight: '',
    job: { status: 0 },
    running: false,
    runningModel: false,
    outnameModel: '',
    modelCompleted: false,
    traits: ["canopy_height","leaf_angle_mean","leaf_angle_alpha","leaf_angle_beta","leaf_angle_chi","per_cultivar_gboost","abserror_per_cultivar_gboost","avg_error_per_cultivar_gboost"],
    traitsModel: ["abserror_per_cultivar_gboost","avg_error_per_cultivar_gboost","abserror_per_cultivar_gboost"],
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
    readyToDownload() {
      return (this.modelCompleted)
    },
  },
  computed: {
    readyToRunModel() {
      return (this.selectedSeason.length>0) &&
        !!(this.estimators>1) &&
	!!(this.maxDepth>0) &&
	!!(this.maxDepth<51) &&
	!!(this.learningRate>0.0) &&
	!!(this.learningRate<0.51)
    },
    readyToRunLeft() {
      return !!(this.selectedDayLeft>0) &&
	!!(this.modelCompleted) &&
        !!(this.selectedTraitLeft.length>0); 
    },
    readyToRunRight() {
      return !!(this.selectedDayRight>0) &&
	!!(this.modelCompleted) &&
        !!(this.selectedTraitRight.length>0); 
    },
    loggedOut() {
      return this.girderRest.user === null;
    },
  },
  methods: {
    async runModel() {

      this.errorLog = null;
      this.runningModel = true;
      console.log('running model');
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultLeft`,
      )).data
      

      const params = optionsToParameters({
	// convert the string entered for the day to a number
	season: this.selectedSeason,
        estimators: Number(this.estimators),
	depth: Number(this.maxDepth),
	learn: Number(this.learningRate),
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/terraPerCultivarModel?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);
      console.log('model is finished');

      if (this.job.status === 3) {
	// save the model results filename that comes back.  We will need access to the 
	// model results again  later visualizations
	this.outnameModel = outname;
	console.log('model result girder id:',this.outnameModel._id);
        this.runningModel = false;
	// get the model results back and parse them for visualization
        this.resultModel = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);
	this.modelCompleted = true;

     // loop through the array and fix the range,column to be integers.  they come back as strings
     // and this messes up the order of the rows & columns when rendered in vega-lite
      for(let i = 0; i < this.resultModel.length; i++){
        this.resultModel[i].range = Number(this.resultModel[i].range);
        this.resultModel[i].column = Number(this.resultModel[i].column);
      }

      // build the spec here.  Inside this method means that the data item will be available. 
      const chartTitle = 'Average error at each plot across the field during '+this.selectedSeason
      var vegaLiteSpec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v2.0.json',
        title: chartTitle,
        description: 'trait values across the field',
        data: {values: this.resultModel}, 
        mark: {type:'rect', tooltip: {content: "data"}},
        encoding: {
          x: {field: 'column', type: 'ordinal'},
          y: {field: 'range', type: 'ordinal'},
          color: {field: 'avg_error_per_cultivar_gboost' , type: 'quantitative'}
        }
      };
	vegaEmbed(this.$refs.visModel,vegaLiteSpec);
      }
      if (this.job.status === 4) {
        this.runningModel = false;
      }
    },

    async runLeft() {
      this.running = true;
      this.errorLog = null;
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultLeft`,
      )).data


      // Pass this.resultModel to be rendered instead of having a file read by the python method so multiple
      // users can run models. 

      // FIX: when this AJAX call is received on the Python side, the data is just the string "[object object]"

      // const stringifiedData  = JSON.stringify({'data': this.resultModel}) 
      const params = optionsToParameters({
	// convert the string entered for the day to a number
        selectedDay: Number(this.selectedDayLeft),
        selectedTrait: this.selectedTraitLeft,
	modelResultId: this.outnameModel._id,
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
	// we tried here to pass the model data back to the python method, but we don't know how to read it,
	// so it will be easier to pass only the girder Id back and the python method can read the data from girder.
        //`arbor_nova/terraModelDaily?${params}`, {'data': this.resultModel},
        `arbor_nova/terraModelDaily?${params}`, 
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

      // build the spec here.  Inside the method means that the data item will be available. 
      var vegaLiteSpec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v2.0.json',
        description: 'trait values across the field',
        data: {values: this.resultLeft}, 
        mark: {type:'rect', tooltip: {content: "data"}},
        encoding: {
          x: {field: 'column', type: 'ordinal'},
          y: {field: 'range', type: 'ordinal'},
          color: {field: this.selectedTraitLeft , type: 'quantitative'}
        }
      };
	vegaEmbed(this.$refs.visLeft,vegaLiteSpec);
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },


    // this is called when the right field display is desired.  A Vega-Lite spec is used for the rendering.
    // The data for the rendering is retrieved from a girder REST endpoint (..terraTraitDaily). 

    async runRight() {
      this.running = true;
      this.errorLog = null;
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=resultRight`,
      )).data

      // similarly to the left rendering, we'd like to modify the API to receive the model results to allow multiple 
      // executions simulaneously without overright. 
      const params = optionsToParameters({
	// convert the string entered for the day to a number
        selectedDay: Number(this.selectedDayRight),
        selectedTrait: this.selectedTraitRight,
	modelResultId: this.outnameModel._id,
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/terraModelDaily?${params}`,
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
      var vegaLiteSpec = {
        $schema: 'https://vega.github.io/schema/vega-lite/v2.0.json',
        description: 'trait values across the field',
        data: {values: this.resultRight}, 
        mark: {type:'rect', tooltip: {content: "data"}},
        encoding: {
          x: {field: 'column', type: 'ordinal'},
          y: {field: 'range', type: 'ordinal'},
          color: {field: this.selectedTraitRight , type: 'quantitative'}
        }
      };
	vegaEmbed(this.$refs.visRight,vegaLiteSpec);
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },


    // The user has selected to download results, so convert the array to a CSV string and download it.
    // The download is caused by 
    async downloadResults() {

	// iterate through the first row to find the column names
        var csvOutput = ''
	for (var key in this.resultModel[0]) {
	  csvOutput += key+','
	} 
        csvOutput += "\n";

        this.resultModel.forEach(function(row) {

		for (var key in row) {
    		// check if the property/key is defined in the object itself, not in parent
    		if (row.hasOwnProperty(key)) {           
        			//console.log(key, row[key]);
				csvOutput += row[key]+','
    			}
		}
            csvOutput += "\n";
        });
 
	// the csv seems to be created correctly
        //console.log(csvOutput);

	//csvOutput = JSON.stringify(csvOutput)
	console.log(csvOutput.split(0,50))
        const url = window.URL.createObjectURL(new Blob([csvOutput]));
	console.log("url:",url)
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'model_results.csv') //or any other extension;
        document.body.appendChild(link);
        link.click();
	document.body.removeChild(link);
	// the above downloaded an file, but there is an
	// alternate way, if needed here as part of the FileSaver package:
	//saveAs(csvOutput,{type:"text/csv"},"model_prediction.csv");
    },

  }
}
</script>
