<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Histopathology Inference</v-toolbar-title>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.imageFile.click()'>{{ fastaFileName || 'UPLOAD input image file' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="imageFile"
              @change="uploadImageFile($event.target.files[0])"
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
              <b>Run a pretrained neural network on the input image.  
		The image will be resized as needed before inferencing by the network.
              <br><br>
		Once the input files are uploaded, click the "Go" button to begin execution.  Execution may take some time
		depending on the size of the input files being provided.	
		</b>
            </v-card-text>
          </v-card>
        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
        </div>
        <div v-if="runCompleted" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Job Complete  ... 
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
        <template v-if="!running && job.status === 3">
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
  name: 'infer_rhabdo',
  inject: ['girderRest'],
  components: {
    JsonDataTable,
  },
  data: () => ({
    imageFile: {},
    imageFileName: '',
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
      return !!this.imageFileName; 
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
        imageId: this.imageFile._id,
        outputId: outputItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/infer_rhabdo?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.result = (await this.girderRest.get(`item/${outputItem._id}/download`)).data;
	this.runCompleted = true;
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },
    async uploadImageFile(file) {
      if (file) {
        this.runCompleted = false;
        this.imageFileName = file.name;
	//b64encodedFile = btoa(file)
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.imageFile = await uploader.start();
      }
    },

    async downloadResults() {
	// add base64 decoding of image contents
	//b64decoded = atob(this.result)
        const url = window.URL.createObjectURL(new Blob([this.result]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'infer_results.tif') //or any other extension;
        document.body.appendChild(link);
        link.click();
    },
  }
}
</script>
