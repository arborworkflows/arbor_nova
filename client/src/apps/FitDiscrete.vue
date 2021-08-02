<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Fit Discrete</v-toolbar-title>
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
            <v-select label="Select a Model" v-model="selectedModel" :items="models" />
          </v-flex>
	  <v-flex xs12>
	    <v-select label="Select a Transformation" v-model="selectedTransformation" :items="transformation" />
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
		    :class="{primary: readyToDownload }"
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
              <b>FitDiscrete</b> is an app that runs the fitDiscrete function in the R package geiger (Pennell et al., 2014). This function fits various likelihood models for discrete character evolution. It returns parameter estimates and a maximum likelihood estimate.
              <br><br>
              1. Upload your table (.csv) and tree (Newick, .phy).
              <br><br>
              2. Select the desired column to run fitDiscrete on.
              <br><br>
	      3. Select the desired Model and Transformation.
	      <br>
	      Models include: 
	      <br>
	      <ul>
	      	<li>ER (Equal-Rates)</li>
		<li>SYM (Symmetric)</li>
		<li>ARD (All Rates Different)</li>
		<li>meristic (transitions occur in a stepwise fashion without skipping intermediate steps)</li>
	      </ul>
	      <br>
	      Transformations include: 
	      <br>
	      <ul>
		<li>none (rate constancy)</li>
		<li>EB (Early-burst)</li>
		<li>lambda (transforms the tree so that lambda values near 0 cause the phylogeny to become more star-like, and a lambda value of 1 recovers the "none" model)</li>
		<li>kappa (raises all branch lengths to an estimated power (kappa))</li>
		<li>delta (raises all node depths to an estimated power (delta))</li>
		<li>white (white-noise)</li>
	      </ul>
              <br>
	      4. Click GO.
              <br><br>
	      <br><br>
	      Source cited: Pennel, M.W., J.M. Eastman, G.J. Slater, J.W. Brown, J.C. Uyeda, R.G. FitzJohn, M.E. Alfaro, & L.J. Harmon. 2014. geiger v2.0: an expanded suite of methods for fitting macroevolutionary models to phylogenetic trees. Bioinformatics 30: 2216-2218.
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
          <v-card v-if="result.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>Result summary</v-card-text>
            <json-data-table :data="result" hide-actions/>
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
  name: 'fitdiscrete',
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
    models: ['ER','SYM','ARD','meristic'],
    selectedModel: '',
    transformation: ['none','EB','lambda','kappa','delta','white'],
    selectedTransformation: '',
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
	!!this.selectedTransformation;
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
	selectedTransformation: this.selectedTransformation,
        resultSummaryItemId: resultSummaryItem._id,
        plotItemId: plotItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/fitdiscrete?${params}`,
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
		    if (row.hasOwnProperty(key)) {
			csvOutput += row[key]+','
		    }
		}
	csvOutput += "\n";
   });

   console.log(csvOutput.split(0,50))
   const url = window.URL.createObjectURL(new Blob([csvOutput]));
   console.log("url:",url)
   // Attach it to an <a> tag and click the link. Then remove the tag
   const link = document.createElement('a');
   link.href = url;
   link.setAttribute('download', 'model_results.csv')
   document.body.appendChild(link);
   link.click();
   document.body.removeChild(link);
  },

  }
}
</script>
