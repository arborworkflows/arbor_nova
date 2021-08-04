<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Fit Continuous</v-toolbar-title>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.tableFile.click()'>{{ tableFileName || 'UPLOAD TABLE' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="tableFile"
              @change="uploadTable($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.treeFile.click()'>{{ treeFileName || 'UPLOAD TREE' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="treeFile"
              @change="uploadTree($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-select label="Column" v-model="selectedColumn" :items="columns" />
          </v-flex>
          <v-flex xs12>
            <v-select label="Select Model"  v-model="selectedModel" :items="models" />
          </v-flex>
	  <v-flex xs12>
	    <textarea style="width: 100%" v-model="stdError" placeholder="Input your standard error (Numeric value only)"></textarea>
          </v-flex>
	  <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToRun }"
              :flat="readyToRun"
              :outline="!readyToRun"
              :disabled="!readyToRun"
              @click="run"
            >
              Go
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
              <b>FitContinuous</b> is an app that runs the fitContinuous function in the R package geiger (Pennell et al., 2014). It fits various likelihood models for continuous character evolution and returns parameter estimates and a maximum likelihood estimate.
              <br><br>
              1. Upload your table (.csv) and tree (Newick, .phy). Note: tables are assumed to have species names as row names.
              <br><br>
              2. Select the desired column to run fitContinuous on. 
              <br><br>
	      3. Select the desired Model and input your standard error.
	      <br>
	      Models include:
	      <br>
 	      <ul>
		<li>BM (Brownian Motion)</li> 
		<li>OU (Ornstein-Uhlenbeck)</li>
		<li>EB (Early-Burst)</li>
		<li>rate_trend (diffusion model with linear trend in rates through time)</li>
		<li>lambda (one of the Pagel (1999) models that fits the extent to which the phylogeny predicts covariance among trait values for species)</li>
		<li>kappa (character divergence is related to the number of speciation events between two species)</li>
		<li>delta (time-dependent model of trait evolution)</li>
		<li>mean_trend (sensible only for non-ultrametric trees; directional drift/trend toward smaller or larger values through time)</li>
		<li>white (white-noise)</li>
	      </ul>
	      <br>
              4. Click GO.
              <br><br>
	      <br><br>
	      Sources cited: Pagel M. 1999. Inferring the historical patterns of biological evolution. Nature 401: 877-884.
	      <br>
	      Pennel, M.W., J.M. Eastman, G.J. Slater, J.W. Brown, J.C. Uyeda, R.G. FitzJohn, M.E. Alfaro, & L.J. Harmon. 2014. geiger v2.0: an expanded suite of methods for fitting macroevolutionary models to phylogenetic trees. Bioinformatics 30: 2216-2218.
             
	    </v-card-text>
          </v-card>
          <v-card v-if="table.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>{{ tableFileName }}</v-card-text>
            <json-data-table :data="table" />
          </v-card>
        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
        <template v-if="!running && job.status === 3">

	  <v-card class ="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Maximum-Likelihood Estimate:</b>
		<br></br>
		{{ this.result[0]["lnL"] }}
	    </v-card-text>
	  </v-card>
          <v-card v-if="result.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>Result summary</v-card-text>
            <json-data-table :data="result" hide-actions/>
          </v-card>
	  <v-card class ="mb-4 ml-4 mr-4">
	     <v-card-text>Phenogram Plot</v-card-text>
	     <img :src="plotUrl" style="display: block; margin: auto">
	     </v-card>
        </template>
      </v-layout>
    </v-layout>
  </v-app>
</template>

<script>
import { utils } from '@girder/components/src';
import { csvParse } from 'd3-dsv';
import scratchFolder from '../scratchFolder';
import pollUntilJobComplete from '../pollUntilJobComplete';
import optionsToParameters from '../optionsToParameters';
import JsonDataTable from '../components/JsonDataTable';

export default {
  name: 'fitContinuous',
  inject: ['girderRest'],
  components: {
    JsonDataTable,
  },
  data: () => ({
    tableFile: {},
    table: [],
    treeFile: {},
    tableFileName: '',
    treeFileName: '',
    job: { status: 0 },
    running: false,
    columns: [],
    selectedColumn: null,
    models:['BM','OU','EB','rate_trend','lambda','kappa','delta','mean_trend','white'],
    selectedModel: '',
    stdError: '',
    result: [],
    resultColumns: [],
    plotUrl: '',
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRun() {
      return !!this.treeFileName &&
        !!this.tableFileName &&
        !!this.selectedColumn &&
	!!this.selectedModel &&
	!!this.stdError;
    },

    readyToDownload() {
      return (this.result.length>0 && !this.running && this.job.status===3)
    },

  },
  methods: {
    async run() {
      this.running = true;
      this.errorLog = null;
      const resultSummaryItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data
      const plotItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

      const params = optionsToParameters({
        tableFileId: this.tableFile._id,
        treeFileId: this.treeFile._id,
        selectedColumn: this.selectedColumn,
	model: this.selectedModel,
	stdError: this.stdError,
        resultSummaryItemId: resultSummaryItem._id,
        plotItemId: plotItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/fitcontinuous?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.result = csvParse((await this.girderRest.get(`item/${resultSummaryItem._id}/download`)).data);
        this.resultColumns = this.result.columns.map(d => ({text: d, value: d, sortable: false}));
        this.plotUrl = `${this.girderRest.apiRoot}/item/${plotItem._id}/download`;
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },
    async uploadTable(file) {
      if (file) {
        this.tableFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder}); 
        this.tableFile = await uploader.start();
        const reader = new FileReader();
        reader.addEventListener('loadend', e => {
          const text = e.srcElement.result;
          this.table = csvParse(text);
          this.columns = csvParse(text).columns;
        });
        reader.readAsText(file);
      }
    },
    async uploadTree(file) {
      if (file) {
        this.treeFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest,  parent: this.scratchFolder});
        this.treeFile = await uploader.start();
      }
    },


    async downloadResults() {
	// iterate through the first row to find the column names
        var csvOutput = ''
	for (var key in this.result[0]) {
	  csvOutput += key+','
	} 
        csvOutput += "\n";

        this.result.forEach(function(row) {
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
	// this is an old but still normal way to download a file, attach it to an 
	// <a> tag and click the link.  We then remove the tag after downloaing. 
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'model_results.csv') //or any other extension;
        document.body.appendChild(link);
        link.click();
	document.body.removeChild(link);
    },

  }
}
</script>
