<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">PolyA-tail</v-toolbar-title>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.fastaFile.click()'>{{ fastaFileName || 'UPLOAD FASTA' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="fastaFile"
              @change="uploadFastaFile($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.linkerFile.click()'>{{ linkerFileName || 'UPLOAD LINKER' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="linkerFile"
              @change="uploadLinkerFile($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.transcriptFile.click()'>{{ transcriptFileName || 'UPLOAD TRANSCRIPT' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="transcriptFile"
              @change="uploadTranscriptFile($event.target.files[0])"
            >
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
          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToDownload }"
              :flat="readyToDownload"
              :outline="!readyToDownload"
              :disabled="!readyToDownload"
              @click="downloadResults"
            >
              Download Results 
            </v-btn>
          </v-flex>
        </v-container>
      </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b>The PolyA-tail analysis. Polyadenylation is the addition of a poly(A) tail to a messenger RNA. 
		The poly(A) tail consists of multiple adenosine monophosphates.  This method scans the input file looking for 
		PolyA tails.  A list of the discovered tails is output when the method finishes. 	
              <br><br>
		Once all the input files are uploaded, click the "Go" button to begin execution.  Execution may take some time
		depending on the size of the input files being scanned.	
		</b>
            </v-card-text>
          </v-card>
        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
        </div>
        <div v-if="runCompleted" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Processing Output ... 
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
        <template v-if="!running && job.status === 3">
          <v-card v-if="result.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>PolyA Tail Results</v-card-text>
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
  name: 'polya',
  inject: ['girderRest'],
  components: {
    JsonDataTable,
  },
  data: () => ({
    fastaFile: {},
    linkerFile: {},
    transcriptFile: {},
    fastaFileName: '',
    linkerFileName: '',
    transcriptFileName: '',
    job: { status: 0 },
    running: false,
    result: [],
    resultColumns: [],
    resultString:  '',
    runCompleted: false,
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRun() {
      return !!this.fastaFileName &&
        !!this.linkerFileName &&
        !!this.transcriptFileName; 
    },
    readyToDownload() {
      return (this.runCompleted)
    },
  },
  methods: {
    async run() {
      this.running = true;
      this.errorLog = null;
      const outputItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

      const params = optionsToParameters({
        fastaId: this.fastaFile._id,
        linkerId: this.linkerFile._id,
        transcriptId: this.transcriptFile._id,
        outputId: outputItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/polya?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.resultString = (await this.girderRest.get(`item/${outputItem._id}/download`)).data;
	// generate a sample of the first 25 entries of the file
	this.resultString = this.resultString.split('\n').slice(0,25).join('\n')
        this.result = csvParse(this.resultString);
        this.resultColumns = this.result.columns.map(d => ({text: d, value: d, sortable: false}));
	this.runCompleted = true;
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },
    async uploadLinkerFile(file) {
      if (file) {
        this.runCompleted = false;
        this.linkerFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.linkerFile = await uploader.start();
      }
    },
    async uploadTranscriptFile(file) {
      if (file) {
        this.runCompleted = false;
        this.transcriptFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.transcriptFile = await uploader.start();
      }
    },
    async uploadFastaFile(file) {
      if (file) {
        this.runCompleted = false;
        this.fastaFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.fastaFile = await uploader.start();
      }
    },

    // a Blob had to be used to download large files.  Otherwise the browser can choke on a 
    // large file. 

    async downloadResults() {
	console.log('resultString beginning: ',this.resultString.split(0,200));
	//forceFileDownload(this.resultString);
        const url = window.URL.createObjectURL(new Blob([this.resultString]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'polyA_download.csv') //or any other extension;
        document.body.appendChild(link);
        link.click();
    },


  }
}
</script>
