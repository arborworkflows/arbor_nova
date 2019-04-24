/* src/plugins/girder.js */
import Vue from 'vue';
import Girder, { RestClient } from '@girder/components/src';
import { API_URL, STATIC_PATH } from "../constants";

// Install the Vue plugin that lets us use the components
Vue.use(Girder);

// Create the axios-based client to be used for all API requests
const girderRest = new RestClient({apiRoot: API_URL});

// This is passed to our Vue instance; it will be available in all components
const GirderProvider = {
  girderRest,
};
export default GirderProvider;
