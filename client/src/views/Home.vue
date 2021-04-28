<template>
<v-app>
  <div class="grey lighten-3 root">
    <v-container
      grid-list-xl
    >
      <v-layout row wrap>

 <v-dialog
        v-model="dialog"
        width="500"
        persistent
      >  
        <v-card>
          <v-card-title class="headline grey lighten-2">
            Research Use Policy
          </v-card-title>
  
          <v-card-text>
            The algorithms and software provided on this site are
            intended for research purposes only.  This system has
            not been reviewed and approved by the Food and Drug
            Administration or any other US Federal agency for use
            in clinical applications. 
          </v-card-text>
  
          <v-divider></v-divider>
  
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              text
              @click="dialog = false"
            >
              I accept
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <v-dialog
        v-model="loginDialog"
        width="600"
        persistent
      >  
        <v-card>
          <v-card-title class="headline grey lighten-2">
            User Login
          </v-card-title>
          <v-text-field
            label="Please enter your user login"
            v-model="attemptedUserName"
          >
          </v-text-field>
          <v-text-field
             label="Please enter your password"
             v-model="attemptedUserPassword"
             type='password'
          >
          </v-text-field>
          <v-divider></v-divider>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
              color="primary"
              text
              @click="girderComponentLoginWrapper"
            >
              Login
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>


        <v-flex xs12 class="text-xs-center">
          <img src="../assets/FNLCR-logo.png">
        </v-flex>
          <v-flex xs12>
          <v-btn
              block
              @click="loginButton"
            >
            {{ loginText }}
            </v-btn>

          <v-btn
              block
              @click="logout"
            >
            Log out
            </v-btn>
          </v-flex>

        <v-flex xs12>
          <span class="title">Applications</span>
        </v-flex>

        
        <v-flex v-if="loggedIn"
          v-for="(sample, i) in samples"
          :key="i"
          xs4
        >
          <v-card
            class="arborApp"
            flat
            tile
          >
            <v-img
              :src="sample.image"
              height="300px"
            />
            <div
              class="linkOverlay"
              v-on:click.stop="$router.push(sample.route)"
            >
              <div class="linkOverlayText body-2">
                {{ sample.label }}
                <div class="description" v-if="sample.description">
                  {{ sample.description }}
                </div>
              </div>
            </div>
          </v-card>
        </v-flex>

      </v-layout>
    </v-container>
  </div>
</v-app>
</template>

<script>

import { utils } from '@girder/components/src';
import optionsToParameters from '../optionsToParameters';
import { Authentication as GirderAuth } from "@girder/components/src/components";

components: {
    GirderAuth
}



export default {
  name: 'home',
  inject: ['girderRest'],
  data: () => ({
    smallScreen: false,
    dialog: false,
    loginDialog: false,
    girderLoginDialog: false,
    username: '',
    attemptedUserName: '',
    attemptedUserPassword: '',
    token: '',
    user: '',
    loginText: 'Please login here',
    samples: [

      {   
        label: 'RMS Tissue Identification from H&E ROI',
        image: require('../assets/RMS-ROI-segmentation.png'),
        route: 'infer_rhabdo',
        description: 'Segment an ROI from an H&E-stained Rhabdomyosarcoma image',
      },    
      {   
        label: 'Whole Slide RMS Segmentation',
        image: require('../assets/RMS-WSI-segmentation.png'),
        route: 'infer_wsi',
        description: 'Segment an entire H&E-stained Rhabdomyosarcoma WSI by uploading the slide for processing',
      },    
      {   
        label: 'TP53 Mutations',
        image: require('../assets/TP53-mutation.png'),
        route: 'tp53_mutation',
        description: 'Segment for mutations of TP53 at the cellular level',
      },   
      {   
        label: 'Tissue Microarray Classification',
        image: require('../assets/TMIA classification.png'),
        route: 'tmia_classification',
        description: 'Classify biopsies in TMIA as positive/negative for RMS subtypes',
      },   
    ],
  }),

// start with a 'research use only' dialog the first time 
// the page is rendered

created () {
  // ** test here they are not logged in.  If logged in, don't 
  // show the dialog again.
  this.username = localStorage.getItem('inferenceUser')
  if (this.username == null) {
      console.log('not logged in. showing dialog')
      this.dialog = true  
  } else {
   this.loginText = 'Logged in as user: '+this.username
  }
},

// this is used to control the rendering of the apps and anything
// else that isn't visible until the user has logged in
computed: {
 loggedIn() {
      //var usertest = this.girderRest.user ? this.girderRest.user.login : ''
      //console.log('loggedIn: current user:',this.username)
      if (this.username == null) {
        return false
      } else {
        return this.username.length>0
      }
    },
},


methods: {


 // when the user clicks the button to login, open the login dialog

 loginButton() {
  console.log("open dialog to login the user");
  this.loginDialog = true
  //this.girderLoginDialog = true
 
  },



 async girderComponentLoginWrapper() {
    const response =  this.loginFromGirderComponents( this.attemptedUserName,this.attemptedUserPassword)
 },


async loginFromGirderComponents(username, password, otp = null) {

    const GirderTokenLength = 64;
    const OauthTokenPrefix = '#girderToken=';
    const OauthTokenSuffix = '__';

    // Girder's custom headers
    const GirderToken = 'Girder-Token';
    const GirderOtp = 'Girder-OTP';
    const GirderAuthorization = 'Girder-Authorization';

    let auth;
    const headers = {
      [GirderToken]: null,
    };
 
    // try basic authentication  
    headers[GirderAuthorization] = `Basic ${window.btoa(`${username}:${password}`)}`;

    const resp = await this.girderRest.get('user/authentication', {
    headers, auth, withCredentials: false,
    })

    if (resp.status == 200){
      console.log('hooray, you are logged in')
      this.username = this.attemptedUserName
      this.loginDialog = false    
      this.token = resp.data.authToken.token;
      this.user = resp.data.user;
      this.username = this.attemptedUserName
      this.loginText = 'Logged in as user: '+this.username
      // set a local storage that will be persistent across the page reload 
      // this helps the app remember the user logged in when they come back to this
      // Home.vue view
      localStorage.setItem('inferenceUser',this.username)
    } else {
      console.log('sorry. try again')
      localStorage.removeItem('inferenceUser')
      this.username = ''
    }
    console.log('girder login response:',resp)
    return resp;
  },


  async logout() {
      if (!this.username) {
        return;
      } else {
        this.token = null;
        this.user = null;
        this.username = null;
        // remove from local storage so session is over in all pages
        localStorage.removeItem('inferenceUser')
      }
    }

 }  // end methods

}

</script>

<style>
.root {
  display: flex;
  flex-flow: column;
  height: 100%;
  overflow-y: auto;
}

.buttonText {
  margin-right: 8px;
  text-transform: uppercase;
}

.arborApp {
  flex: 1;
  border-radius: 5px;
  overflow: hidden;
  cursor: pointer;
  box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
}

.linkOverlay {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 100%;
  z-index: 1;
  opacity: 0;
  background: rgba(255,255,255,0.2);
  font-size: 300%;
  text-align: center;
  font-weight: bolder;
  cursor: pointer;
  color: white;
}

.linkOverlay:hover {
  opacity: 1;
}

.description {
  font-size: 80%;
  color: lightgray;
}

.linkOverlayText {
  position: absolute;
  bottom: 0px;
  width: 100%;
  background: rgba(0,0,0,0.6);
  padding: 10px;
}
</style>
