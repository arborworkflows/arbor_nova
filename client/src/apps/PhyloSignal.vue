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
              <b>Phylogenetic signal</b> is a measure of the nonindependence among species traits due to their phylogenetic relatedness (Revell et al. 2008).
              <br></br>
	      In this app, you can use either Pagel's Lambda or Blomberg's K to measure phylogenetic signal in a given trait. If the trait you are interested in is discrete, you can also choose between the following models: Equal Rates (ER), Symmetrical (SYM), or All Rates Different (ARD).
	      <br></br>
              1. Upload your table (.csv) and tree (Newick, .phy).
              <br></br>
              2. Select the desired column and a method for the model to use.
              <br></br>
              3. Click GO.
	      <br></br>
	      <br></br>
	      Source cited: Revell, L.J., L.J. Harmon, & D.C. Collar. Phylogenetic Signal, Evolutionary Process, and Rate. <i>Systematic Biology</i>, 57(4): 591-601.
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
	 
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Log-Likelihood (Lambda fixed at 0):</b>
		<br></br>
		{{ this.result[0]["Log-Likelihood (Lambda fixed at 0)"] }}
		<br></br>
		Here, lambda is fixed at 0 (meaning every species is statistically independent of every other species). This number represents the log-likelihood of lambda being 0. 
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Log-Likelihood (Lambda Estimated):</b>
		<br></br>  
		{{ this.result[0]["Log-Likelihood (Lambda estimated)"] }}
		<br></br>
		This result is similar to the one above, except that lambda is estimated and not fixed at 0.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Chi-Squared Test Statistic:</b>  
		<br></br>
		{{ this.result[0]["Chi-Squared Test Statistic"] }}
		<br></br>
		This result is the test statistic obtained when a chi-square test is performed to compare the provided data to the expected chi-square distribution. 
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Chi-Square P Value:</b>
		<br></br>  
		{{ this.result[0]["Chi-Squared P Value"] }}
		<br></br>
		This is the p value obtained from the chi-square test described above.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>AICc Score (Lambda fixed at 0):</b>
		<br></br> 
		{{ this.result[0]["AICc Score (Lambda fixed at 0)"] }}
		<br></br>
		This AICc (AIC with a correction for small sample sizes) score is computed with lambda fixed at 0.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>AICc Score (Lambda Estimated):</b>
		<br></br>  
		{{ this.result[0]["AICc Score (Lambda Estimated)"] }}
		<br></br>
		This AICc score is similar to the one above, except lambda is estimated.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'Lambda'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Lambda Value:</b>  
		<br></br>
		{{ this.result[0]["Lambda Value"] }}
		<br></br>
		This is the lambda value used for  model fitting.
	    </v-card-text>
	  </v-card>

	  <v-card v-if="this.selectedModel === 'K'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Blomberg's K Value:</b>  
		<br></br>
		{{ this.result[0]["K"] }}
		<br></br>
		K is a descriptive statistic that gauges the amount of phylogenetic signal.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'K'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Mean observed variance of PICs:</b>  
		<br></br>
		{{ this.result[0]["vObs"] }}
		<br></br>
		This is the observed variance of phylogenetically independent contrasts (PICs).
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'K'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Mean random variance of PICs:</b>  
		<br></br>
		{{ this.result[0]["vRnd"] }}
		<br></br>
		This is the random variance of PICs obtained through the use of tip shuffling randomization.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'K'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>P value:</b>  
		<br></br>
		{{ this.result[0]["pVal"] }}
		<br></br>
		This is the p value that results from testing the difference between the observed vs random variance of PICs.
	    </v-card-text>
	  </v-card>
	  <v-card v-if="this.selectedModel === 'K'" class="mb-4 ml-4 mr-4">
	    <v-card-text>
		<b>Z-score:</b>  
		<br></br>
		{{ this.result[0]["zScore"] }}
		<br></br>
		This is the z-score that results from testing the difference between the observed vs random variance of PICs.
	    </v-card-text>
	  </v-card>

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
    selectedDiscrete: 'ER',
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

    readyToDownload() {
      return (this.result.length>0 && !this.running && this.job.status===3)
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
	console.log('This is your method:',this.selectedModel);
        this.resultColumns = this.result.columns.map(d => ({text: d, value: d, sortable: false}));
        
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
