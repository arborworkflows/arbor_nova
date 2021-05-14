<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Rhabdomyosarcoma ROI Analysis</v-toolbar-title>
        </v-toolbar>
        <v-spacer/>
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
              <b>This application analyzes an ROI extracted from a whole slide image by executing a neural network that has
		been pre-trained to segment rhabdomyosarcoma tissue subtypes in H&E stained ROIs extracted from  
		whole slide images.  The application expects the input image to be in TIF, Jpeg, or PNG image formats. Pyrmidal files are not 
    supported by this app, only "ordinary" image files.  For pyramidal images, please see the Whole Slide Inferencing app. 
              <br><br>
		Once the input image is displayed below, please click the "Go" button to begin execution.  Execution may take some time
		depending on the size of the input files being provided.  When the analysis is complete, the resulting segmentation
		will be displayed below and will be available for downloading, using the download button. If you would like to segment additional images, please just click "Prepare for Another Image" in between each segmentation operation. This tells the system to reset and prepare to run again.
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


          <div v-if="readyToDisplayInput" xs12 class="text-xs-center mb-4 ml-4 mr-4">
  	    <v-card class="mb-4 ml-4 mr-4">
            <v-card-text>Uploaded Image</v-card-text>
		{{ renderInputImage(uploadedImageUrl) }} 
            </v-card>
	  </div>
    	  <div ref="inputImageDiv" id ="openseadragon1" style="width:1000px;height:800px; margin: auto;"> </div>
        <v-card v-if="running && job.status==0" xs12 class="text-xs-center mb-4 ml-4 mr-4">
            Another user is currently using the system.  Please wait.  Your inferencing job should begin automatically when the previous job completes. 
            <v-progress-linear indeterminate=True></v-progress-linear>
        </v-card>
        <v-card v-if="running && job.status == 2" xs12 class="text-xs-center mb-4 ml-4 mr-4">
            Running (Job Status {{ job.status }}) ... please wait for the output image to show below
          <v-progress-linear indeterminate=True></v-progress-linear>
        </v-card>
        <div v-if="runCompleted" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Job Complete  ... 
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code> 
        <div v-if="!running && job.status === 3">
    	      <v-card class="mb-4 ml-4 mr-4">
                <v-card-text>Segmentation Image</v-card-text>
  		          {{ renderOutputImage(outputImageUrl) }} 
            </v-card>

            <v-card class="mb-4 ml-4 mr-4">
          	 <div ref="outputImageDiv" id ="openseadragon2" style="width:1000px;height:800px; margin: auto"> </div>
            </v-card>

            <v-card align="center" justify="center" class="mt-8 mb-4 ml-4 mr-4">
               <div id="visM" ref="visModel" class="mt-20 mb-4 ml-4 mr-4"></div>
            </v-card>
            <v-card v-if="table.length > 0" class="mt-8 mb-4 ml-4 mr-4">
                <v-card-text>Image Statistics</v-card-text>
                <json-data-table :data="table" />
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
import vegaEmbed from 'vega-embed';
import { Authentication as GirderAuth } from "@girder/components/src/components";



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
    stats: [],
    table: [],
    resultColumns: [],
    resultString:  '',
    runCompleted: false,
    uploadInProgress: false,
    outputImageUrl: '',
    inputDisplayed:  false,
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
      return !!this.imageFileName; 
    },
    readyToDownload() {
      return (this.runCompleted)
    },
    uploadIsHappening() {
      return (this.uploadInProgress)
    },
  },

  methods: {

    // method is added here to enable openSeadragon to render into a div defined in the vue template
    // above.  This code is re-executed for each change, so the code is gated to only run once 
    renderInputImage(imageurl) {
       if (this.inputDisplayed == false) {
          this.osd_viewer  =  OpenSeadragon( {
	  element: this.$refs.inputImageDiv, 
	  maxZoomPixelRatio: 4.0,
          prefixUrl: "/static/arbornova/images/",
          tileSources: {
            type: 'image',
            url:   imageurl
    	    }
	});
        console.log('openseadragon input finished')
	this.inputDisplayed = true
	}
    },

    // method is added here to enable openSeadragon to render the output image into a div defined in the vue template
    // above.  This code is re-executed for each change, so the code is gated to only run once 
    renderOutputImage(imageurl) {
       if ((this.outputDisplayed == false) & (this.outputImageUrl.length > 0)) {
      console.log('output url:',imageurl)
      var viewer2 =  OpenSeadragon( {
	element: this.$refs.outputImageDiv, 
	maxZoomPixelRatio: 4.0,
        prefixUrl: "/static/arbornova/images/",
        tileSources: {
          type: 'image',
          url:   imageurl
    	  }
	});
        console.log('openseadragon output finished')
	this.outputDisplayed = true
	}
    },

    async run() {
      this.running = true;
      this.errorLog = null;

      // create a spot in Girder for the output of the REST call to be placed
      const outputItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

     // create a spot in Girder for the output of the REST call to be placed
      const statsItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=stats`,
      )).data
      
      // build the params to be passed into the REST call
      const params = optionsToParameters({
        imageId: this.imageFile._id,
        outputId: outputItem._id,
        statsId: statsItem._id
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

        // get the stats returned
        this.stats = (await this.girderRest.get(`item/${statsItem._id}/download`,{responseType:'text'})).data;
        console.log('returned stats',this.stats)
        console.log('parsed stats',this.stats.ARMS, this.stats.ERMS,this.stats.necrosis)
        // copy this data to a state variable for rendering in a table
        this.data = [this.stats]
        this.data.columns = ['ARMS','ERMS','necrosis','stroma']
        // render by updating the this.table model
        this.table = this.data


        // render the image statistics below the image

        // build the spec here.  Inside the method means that the data item will be available. 
        let titleString = 'Percentage of the slide positive for each tissue class'

        var vegaLiteSpec = {
            "$schema": "https://vega.github.io/schema/vega-lite/v4.json",
            "description": "A simple bar chart with embedded data.",
             title: titleString,
              "height": 450,
              "width": 600,
              "autosize": {
                "type": "fit",
                "contains": "padding"
              },
            "data": {
              "values": [
                {"Class": "ARMS","percent": this.stats.ARMS}, 
                {"Class": "ERMS","percent": this.stats.ERMS}, 
                {"Class": "Stroma","percent": this.stats.stroma}, 
                {"Class": "Necrosis","percent": this.stats.necrosis}

              ]
            },
           "layer": [{
              "mark": "bar"
            }, {
              "mark": {
                "type": "text",
                "align": "center",
                "baseline": "bottom",
                "fontSize": 13,
                "dx": 0
              },
              "encoding": {
                "text": {"field": "percent", "type": "quantitative"}
              }
            }],
            "encoding": {
              "x": {"field": "Class", "type": "ordinal","title":"Tissue Classification"},
              "y": {"field": "percent", "type": "quantitative","title":"Percent of tissue positive for each class"},
              "color": {
                  "field": "Class",
                  "type":"nominal",
                  "scale": {"domain":["ARMS","ERMS","Necrosis","Stroma"],"range": ["blue","red","yellow","lightgreen"]}
                  }
            }
          };
          // render the chart with options to save as PNG or SVG, but other options turned off
          vegaEmbed(this.$refs.visModel,vegaLiteSpec,
                 {padding: 10, actions: {export: true, source: false, editor: false, compiled: false}});



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
