<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">MYOD1 Mutation Positive/Negative</v-toolbar-title>
          </v-toolbar>
          <v-spacer/>
          <v-container fluid>

          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.imageFile.click()'>{{ imageFileName || 'UPLOAD Whole Slide Image' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="imageFile"
              @change="uploadImageFile($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.segmentFile.click()'>{{ segmentFileName || 'UPLOAD Segmentation Mask' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="segmentFile"
              @change="uploadSegmentationFile($event.target.files[0])"
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
          <v-flex xs12>
            <v-btn
              block
              :class="{ primary: readyToDownload }"
              :flat="readyToDownload"
              :outline="!readyToDownload"
              :disabled="!readyToDownload"
              @click="reset"
            >
              Prepare For Another Image 
            </v-btn>
          </v-flex>
        </v-container>
      </v-navigation-drawer>
      <v-layout column justify-start fill-height style="margin-left: 400px">
          <v-card class="ma-4">
            <v-card-text>
              <b>This application segments a whole slide image by executing a neural network that has
                  been pre-trained to identify for MYOD1 mutations in rhabdomyosarcoma tissue subtypes in H&E stained   
                  whole slide images.  Uploaded images can be in Aperio (.svs) format or they can be pyramidal TIF files.
                            <br><br>
                  After selecting an image for upload, be patient during the upload process. Once the input image is displayed below, please click the "Go" button to begin execution.  Execution may take up to several minutes,
                  depending on the size of the input image being provided.  When the analysis is complete, the resulting classification and confidence information 
                  will be displayed below and will be available for downloading, using the download button.  If you would like to classify additional images, please just click "Prepare for Another Image" in between each segmentation operation. This tells the system to reset and prepare to run again.  
                            <br><br>
                  We are delighted that you are trying our early release system for rhabdomyosarcoma analysis. Thank you.  
                  If you have any questions while using our system, please feel free to email Dr. Yanling Liu at liuy5@mail.nih.gov.  
                </b>
            </v-card-text>
          </v-card>
          <div v-if="uploadIsHappening" xs12 class="text-xs-center mb-4 ml-4 mr-4">
           Image Upload in process...
           <v-progress-linear indeterminate=True></v-progress-linear>
        </div>
        <div v-if="inputReadyForDisplay">
          <div  xs12 class="text-xs-center mb-4 ml-4 mr-4">
            <v-card class="mb-4 ml-4 mr-4">
              <v-card-text>Uploaded Image</v-card-text>
                <img :src="inputImageUrl" style="display: block; margin: auto"> 
              </v-card>
          </div>
        </div>

        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ... please wait for the output to show below.  This will take several minutes.
          <v-progress-linear indeterminate=True></v-progress-linear>
        </div>
        <div v-if="runCompleted" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Job Complete  ... 
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code> 
        <div v-if="segmentReadyForDisplay">
  	      <v-card class="mb-4 ml-4 mr-4">
            <v-card-text>Segmentation Image</v-card-text>
               <img :src="segmentImageUrl" style="display: block; margin: auto"> 
          </v-card>
        </div>
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
import OpenSeadragon from 'openseadragon';

export default {
  name: 'myod1',
  inject: ['girderRest'],
  components: {
    JsonDataTable,
  },
  data: () => ({
    imageFile: {},
    imageFileName: '',
    segmentFile: {},
    segmentFileName: '',
    imagePointer: '',
    imageBlob: [],
    uploadedImageUrl: '',
    job: { status: 0 },
    readyToDisplayInput: false,
    readyToDisplaySegmentation: false,
    running: false,
    thumbnail: [],
    result: [],
    resultColumns: [],
    resultString:  '',
    runCompleted: false,
    uploadInProgress: false,
    segmentUploadInProgress: false,
    inputImageUrl: '',
    segmentImageUrl: '',
    inputDisplayed:  false,
    segmentDisplayed:  false,
    outputDisplayed:  false,
    osd_viewer: [],
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRun() {
      return !!(this.imageFileName && this.segmentFileName); 
    },
    readyToDownload() {
      return (this.runCompleted)
    },
    uploadIsHappening() {
      return (this.uploadInProgress)
    },
    segmentUploadIsHappening() {
      return (this.segmentUploadInProgress)
    },
    inputReadyForDisplay() {
      return this.inputDisplayed
    },
    segmentReadyForDisplay() {
      return this.segmentDisplayed
    }
  },

  methods: {

    // method here to create and display a thumbnail of an arbitrarily large whole slilde image.
    // This code is re-executed for each UI change, so the code is gated to only run once 

    async renderInputImage() {
       if (this.inputDisplayed == false) {

        // create a spot in Girder for the output of the REST call to be placed
          const outputItem = (await this.girderRest.post(
            `item?folderId=${this.scratchFolder._id}&name=thumbnail`,
          )).data

        // build the params to be passed into the REST call
        const params = optionsToParameters({
          imageId: this.imageFile._id,
          outputId: outputItem._id,
        });
        // start the job by passing parameters to the REST call
        this.job = (await this.girderRest.post(
          `arbor_nova/wsi_thumbnail?${params}`,
        )).data;

          // wait for the job to finish
          await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

          if (this.job.status === 3) {
            this.running = false;
            // pull the URL of the output from girder when processing is completed. This is used
            // as input to an image on the web interface
            this.thumbnail = (await this.girderRest.get(`item/${outputItem._id}/download`,{responseType:'blob'})).data;
            // set this variable to display the resulting output image on the webpage 
            this.inputImageUrl = window.URL.createObjectURL(this.thumbnail);
          }

          console.log('render input finished')
	        this.inputDisplayed = true
	     }
    },

   async renderSegmentImage() {
       if (this.segmentDisplayed == false) {
          this.running = false;
          // pull the URL of the output from girder
          this.thumbnail = (await this.girderRest.get(`file/${this.segmentFile._id}/download`,{responseType:'blob'})).data;
          // set this variable to display the resulting output image on the webpage 
          this.segmentImageUrl = window.URL.createObjectURL(this.thumbnail);
          console.log('render segment finished')
	        this.segmentDisplayed = true
	     }
    },



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
        segmentId: this.segmentFile._id,
        statsId: outputItem._id,
      });
      // start the job by passing parameters to the REST call
      this.job = (await this.girderRest.post(
        `arbor_nova/myod1?${params}`,
      )).data;

      // wait for the job to finish
      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
	      // pull the URL of the output from girder when processing is completed. This is used
	      // as input to an image on the web interface
        this.result = (await this.girderRest.get(`item/${outputItem._id}/download`,{responseType:'blob'})).data;
	      // set this variable to display the resulting output on the webpage 
        this.outputUrl = window.URL.createObjectURL(this.result);
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
        this.uploadInProgress = true;
        this.imageFile = await uploader.start();
        // display the uploaded image on the webpage
        this.uploadInProgress = false;
	      console.log('displaying input image...');
        //this.imageBlob = (await this.girderRest.get(`file/${this.imageFile._id}/download`,{responseType:'blob'})).data;
        //this.uploadedImageUrl = window.URL.createObjectURL(this.imageBlob);
	      //console.log('createObjURL returned: ',this.uploadedImageUrl);
        this.readyToDisplayInput = true;
        this.renderInputImage();
      }
    },


    async uploadSegmentationFile(file) {
      if (file) {
        this.runCompleted = false;
        this.segmentFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.segmentUploadInProgress = true;
        this.segmentFile = await uploader.start();
        // display the uploaded image on the webpage
        this.segmentUploadInProgress = false;
	      console.log('received segmentation image...');
        //this.imageBlob = (await this.girderRest.get(`file/${this.imageFile._id}/download`,{responseType:'blob'})).data;
        //this.uploadedImageUrl = window.URL.createObjectURL(this.imageBlob);
	      //console.log('createObjURL returned: ',this.uploadedImageUrl);
        this.readyToDisplaySegmentation = true;
        this.renderSegmentImage();
      }
    },



    // download the segmentation image result when requested by the user
    async downloadResults() {
        const url = window.URL.createObjectURL(this.result);
	      console.log("url:",url)
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'infer_results.json') 
        document.body.appendChild(link);
        link.click();
	      document.body.removeChild(link);
    },

    // reload the page to allow the user to process another image.
    // this clears all state and image displays. The scroll command
    // resets the browser to the top of the page. 
    reset() {
      window.location.reload(true);
      window.scrollTo(0,0);
    },
  }
}
</script>
