<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Phylogenetic Signal</v-toolbar-title>
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
            <v-select label="Select a Column to use for the model" v-model="selectedColumn" :items="columns" />
          </v-flex>
          <v-flex xs12>
            <v-select label="Select the Model method" v-model="selectedModel" :items="models" />
          </v-flex>
	  <v-flex xs12>
	    <v-select label="Select the Discrete model type (ignored if Continuous)" v-model="selectedDiscrete" :items="discreteModels" />
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
      </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b> Add motivating phylosignal description here </b>
              <br></br>
              1. Upload your table (.csv) and tree (Newick, .phy).
              <br></br>
              2. Select the desired column and a method for the model to use.
              <br></br>
              3. Click GO.
            </v-card-text>
          </v-card>
          <v-card v-if="table.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>{{ tableFileName }}</v-card-text>
            <json-data-table :data="table" />
            <h1>{{ log(tableObject) }}</h1>
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
	  <v-card>
	    <v-card-text>Testing parse: {{ parsetest }}</v-card-text>
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
  name: 'asr',
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
    models: ['Lambda','K'],
    selectedModel: '',
    discreteModels: ['ER','SYM','ARD'],
    selectedDiscrete: '',
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
        this.selectedModel.length>0 &&
        this.selectedColumn.length>0;
    },
  },
  methods: {
   log(message) {
     console.log('method call:',message);
   },

    async run() {
      this.running = true;
      this.errorLog = null;
      const resultSummaryItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

      const params = optionsToParameters({
        tableFileId: this.tableFile._id,
        treeFileId: this.treeFile._id,
        selectedColumn: this.selectedColumn,
        method: this.selectedModel,
	selectedDiscrete: this.selectedDiscrete,
        resultSummaryItemId: resultSummaryItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/phylosignal?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.result = csvParse((await this.girderRest.get(`item/${resultSummaryItem._id}/download`)).data);
	console.log('here is the TABLE:',this.result);
	//console.log(this.result.);
        this.resultColumns = this.result.columns.map(d => ({text: d, value: d, sortable: false}));
        //const parsetest = parse(this.result)
        
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
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent:this.scratchFolder});
        this.treeFile = await uploader.start();
      }
    },


  }
}
</script>
