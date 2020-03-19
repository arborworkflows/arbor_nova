<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Rhabdomyosarcoma ROI Analysis</v-toolbar-title>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.imageFile.click()'>{{ fastaFileName || 'UPLOAD input ROI image' }}</v-btn>
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
              <b>This application analyzes an ROI extracted from a whole slide image by executing a neural network that has
		been pre-trained to segment rhabdomyosarcoma tissue subtypes in H&E stained ROIs extracted from  
		whole slide images.  The application expects the input image to be in TIF, Jpeg, or PNG image formats.
		The image will be resized as needed before being analyzed by the network.
              <br><br>
		Once the input image is uploaded, please click the "Go" button to begin execution.  Execution may take some time
		depending on the size of the input files being provided.  When the analysis is complete, the resulting segmentation
		will be displayed below and will be available for downloading, using the download button.  
              <br><br>
		We are delighted that you are trying our early release system for rhabdomyosarcoma analysis. Thank you.  
		If you have any questions while using our system, please feel free to email Dr. Yanling Liu at liuy5@mail.nih.gov.  
		</b>
            </v-card-text>
          </v-card>
          <div v-if="readyToDisplayInput" xs12 class="text-xs-center mb-4 ml-4 mr-4">
  	    <v-card class="mb-4 ml-4 mr-4">
            <v-card-text>Uploaded Image</v-card-text>
              <img :src="uploadedImageUrl" style="display: block; margin: auto">
            </v-card>
	</div>
        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
        </div>
        <div v-if="runCompleted" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Job Complete  ... 
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
        <template v-if="!running && job.status === 3">
  	  <v-card class="mb-4 ml-4 mr-4">
            <v-card-text>Segmentation Image</v-card-text>
            <img :src="outputImageUrl" style="display: block; margin: auto">
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
  name: 'infer_rhabdo',
  inject: ['girderRest'],
  components: {
    JsonDataTable,
  },
  data: () => ({
    imageFile: {},
    imageFileName: '',
    imagePointer: '',
    imageBlob: [],
    uploadedImageUrl: '',
    job: { status: 0 },
    readyToDisplayInput: false,
    running: false,
    result: [],
    resultColumns: [],
    resultString:  '',
    runCompleted: false,
    outputImageUrl: '',
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

      // create a spot in Girder for the output of the REST call to be placed
      const outputItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

      // build the params to be passed into the REST call
      const params = optionsToParameters({
        imageId: this.imageFile._id,
        outputId: outputItem._id,
      });
      // start the job by passing parameters to the REST call
      this.job = (await this.girderRest.post(
        `arbor_nova/infer_rhabdo?${params}`,
      )).data;

      // wait for the job to finish
      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
	// pull the URL of the output from girder when processing is completed. This is used
	// as input to an image on the web interface
        this.result = (await this.girderRest.get(`item/${outputItem._id}/download`,{responseType:'blob'})).data;
	// set this variable to display the resulting output image on the webpage 
        this.outputImageUrl = window.URL.createObjectURL(this.result);
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
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.imageFile = await uploader.start();
        // display the uploaded image on the webpage
	console.log('displaying input image...');
        this.imageBlob = (await this.girderRest.get(`file/${this.imageFile._id}/download`,{responseType:'blob'})).data;
        this.uploadedImageUrl = window.URL.createObjectURL(this.imageBlob);
	console.log('createObjURL returned: ',this.uploadedImageUrl);
        this.readyToDisplayInput = true;
      }
    },

    async downloadResults() {
        const url = window.URL.createObjectURL(this.result);
	console.log("url:",url)
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'infer_results.png') //or any other extension;
        document.body.appendChild(link);
        link.click();
	document.body.removeChild(link);
	// the above downloaded an file, but there is an
	// alternate way, if needed here as part of the FileSaver package:
	//saveAs(this.result,{type:"image/png"},"filesaver.png");
    },
  }
}
</script>
