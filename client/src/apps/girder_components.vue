<template>
  <v-app>
      <v-navigation-drawer >
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Rhabdomyosarcoma WSI Segment</v-toolbar-title>
        </v-toolbar>
        <v-list>
          <nav-link
            class="mb-1 font-weight-bold"
            title="Components"
          />
          <nav-link
            title="Authentication"
            href="#auth"
          />
          <nav-link
            title="Upload"
            href="#upload"
          />
          <nav-link
            title="Search"
            href="#search"
          />
          <nav-link
            title="File manager"
            href="#file-manager"
          />
          <nav-link
            title="Job list"
            href="#job-list"
          />
      </v-list>
      </v-navigation-drawer>
       <v-main>
      <v-container>
        <v-col
          xl="8"
          offset-xl="2"
          lg="10"
          offset-lg="1"
          md="12"
          offset-md="0"
        >
          <div class="display-3">
            Girder Web Components
          </div>
          <div class="title mb-1">
            A Vue + Vuetify library for interacting with
            <a href="https://www.kitware.com/">Kitware's</a>
            data management platform,
            <a href="https://girder.readthedocs.io/en/stable/">Girder</a>
          </div><img
            v-for="badge in badges"
            :key="badge"
            :src="badge"
            class="pr-3"
          >
          <v-row class="ma-0">
            <div class="title mb-1">
              This demo integrates with
              <a href="https://data.kitware.com">data.kitware.com</a>
            </div>
            <v-switch
              v-model="$vuetify.theme.dark"
              class="mx-4 my-0"
              hide-details="hide-details"
              label="Dark theme"
            />
          </v-row><a id="auth" />
          <headline
            title="girder-auth"
            link="src/components/Authentication/Authentication.vue"
            description="allows users to authenticate with girder"
          />
          <v-row class="mb-2">
            <v-switch
              v-model="authRegister"
              class="ma-2"
              hide-details="hide-details"
              label="register"
            />
            <v-switch
              v-model="authOauth"
              class="ma-2"
              hide-details="hide-details"
              label="oauth"
            />
          </v-row><template v-if="loggedOut">
            <girder-auth
              :key="girderRest.token"
              :force-otp="false"
              :register="authRegister"
              :oauth="authOauth"
              :forgot-password-url="forgotPasswordUrl"
            />
          </template><template v-else>
            <v-btn
              v-if="!loggedOut"
              color="primary"
              @click="girderRest.logout()"
            >
              Log Out
              <v-icon class="pl-2">
                $vuetify.icons.logout
              </v-icon>
            </v-btn>
          </template><a id="upload" />
          <headline
            title="girder-upload"
            link="src/components/Upload.vue"
            description="upload files to a specified location in girder"
          />
          <v-card>
            <girder-upload
              :dest="uploadDest"
              :post-upload="postUpload"
            />
          </v-card><a id="search" />
          <headline
            title="girder-search"
            link="src/components/Search.vue"
            description="provides global search functionality"
          />
          <v-toolbar color="primary">
            <girder-search @select="handleSearchSelect" />
          </v-toolbar>
          <v-row>
            <v-col
              class="pr-4"
              xl="8"
              lg="8"
              md="6"
              sm="12"
            >
              <a id="file-manager" />
              <headline
                title="girder-file-manager"
                link="src/components/Snippet/FileManager.vue"
                description="a wrapper around girder-data-browser. It packages the browser with
                defaults including folder creation, item upload, and a breadcrumb bar"
              />
            </v-col>
            <v-col class="pa-0">
              <a id="data-details" />
              <headline
                title="girder-data-details"
                link="src/components/DataDetails.vue"
                description="in-depth information and controls for a single folder or item, or
                batch operations for groups of objects."
              />
            </v-col>
          </v-row>
          <v-row>
            <v-switch
              v-model="selectable"
              class="ma-2"
              hide-details="hide-details"
              label="Select"
            />
            <v-switch
              v-model="dragEnabled"
              class="ma-2"
              hide-details="hide-details"
              label="Draggable"
            />
            <v-switch
              v-model="newFolderEnabled"
              class="ma-2"
              hide-details="hide-details"
              label="New Folder"
            />
            <v-switch
              v-model="uploadEnabled"
              class="ma-2"
              hide-details="hide-details"
              label="Upload"
            />
            <v-switch
              v-model="rootLocationDisabled"
              class="mt-2"
              hide-details="hide-details"
              label="Root Disabled"
            />
          </v-row>
          <v-row>
            <v-col
              class="pr-4"
              lg="8"
              md="6"
              sm="12"
            >
              <girder-file-manager
                ref="girderFileManager"
                v-model="selected"
                :items-per-page-options="[10, 20, -1]"
                :drag-enabled="dragEnabled"
                :new-folder-enabled="newFolderEnabled"
                :selectable="selectable"
                :location.sync="location"
                :root-location-disabled="rootLocationDisabled"
                :upload-multiple="uploadMultiple"
                :upload-enabled="uploadEnabled"
                @dragend="dragend"
              />
              <v-card
                v-if="dragEnabled"
                class="mt-4"
                @dragenter.prevent=""
                @dragover.prevent=""
                @drop="drop"
              >
                <v-card-title>Drop Zone</v-card-title>
                <v-card-text>
                  <p v-if="!(dropped.length)">
                    Drag a row here to see results
                  </p>
                  <ul
                    v-for="{ item } in dropped"
                    v-else
                    :key="item._id"
                    class="header"
                  >
                    <li>type: {{ item._modelType }}</li>
                    <li>name: {{ item.name }} </li>
                    <li>size: {{ item.size }}</li>
                  </ul>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col
              class="pl-0"
              lg="4"
              md="6"
              sm="12"
            >
              <girder-data-details
                :value="detailsList"
                @action="handleAction"
              />
            </v-col>
          </v-row><a id="job-list" />
          <headline
            title="girder-job-list"
            link="src/components/Job/JobList.vue"
            description="display and filter girder jobs"
          />
          <girder-job-list /><a id="access-control" />
          <headline
            title="girder-access-control"
            link="src/components/AccessControl.vue"
            description="access controls for folders and items"
          />
          <girder-access-control :model="uploadDest" /><a id="upsert-folder" />
          <headline
            title="girder-upsert-folder"
            link="src/components/UpsertFolder.vue"
            description="create and edit folders"
          />
          <v-switch
            v-model="upsertEdit"
            label="Edit Mode"
          />
          <v-card>
            <girder-upsert-folder
              :location="uploadDest"
              :edit="upsertEdit"
            />
          </v-card><a id="breadcrumb" />
          <headline
            title="girder-breadcrumb"
            link="src/components/Breadcrumb.vue"
            description="filesystem path breadcrumb"
          />
          <v-card class="pa-4">
            <girder-breadcrumb :location="uploadDest" />
          </v-card>
        </v-col>
      </v-container>
    </v-main>
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
