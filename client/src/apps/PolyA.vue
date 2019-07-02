<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">PolyA-tail</v-toolbar-title>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.tableFile.click()'>{{ fastaFileName || 'UPLOAD FASTA' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="fastaFile"
              @change="uploadTable($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.treeFile.click()'>{{ linkerFileName || 'UPLOAD LINKER' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="linkerFile"
              @change="uploadTree($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.treeFile.click()'>{{ transcriptFileName || 'UPLOAD TRANSCRIPT' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="transcriptFile"
              @change="uploadTree($event.target.files[0])"
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
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
        <template v-if="!running && job.status === 3">
          <v-card v-if="result.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>Model fit summary</v-card-text>
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
    fastaFileId: '',
    linkerFileId: '',
    transcriptFileId: '',
    job: { status: 0 },
    running: false,
    result: [],
    plotUrl: '',
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRun() {
      return !!this.fastaFileId &&
        !!this.linkerFileId &&
        !!this.transcriptFileId; 
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
        fastaId: this.fastaFileId,
        linkerId: this.linkerFileId,
        transcriptId: this.transcriptFileId,
        outputId: outputItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/polya?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.result = csvParse((await this.girderRest.get(`item/${modelFitSummaryItem._id}/download`)).data);
        this.resultColumns = this.result.columns.map(d => ({text: d, value: d, sortable: false}));
        this.plotUrl = `${this.girderRest.apiRoot}/item/${plotItem._id}/download`;
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },
    async uploadLinkerFile(file) {
      if (file) {
        this.linkerFileId = file.name;
      }
    },
    async uploadTranscriptFile(file) {
      if (file) {
        this.transcriptFileId = file.name;
      }
    },
    async uploadFastaFile(file) {
      if (file) {
        this.fastaFileId = file.name;
      }
    },
  }
}
</script>
