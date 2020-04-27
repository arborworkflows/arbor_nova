<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">Sensor Trait Explorer</v-toolbar-title>
          <v-spacer/>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
	    <label for="sDay">Enter the day in the season</label>
	   <div id="dayDiv">
              <input type="text" v-model="selectedDay">
	   </div>
          </v-flex>
          <v-flex xs12>
            <v-select label="Selected Trait to Display" v-model="selectedTrait" :items="traits" />
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
              <b>Display Trait Values on selected days in the season.</b> Select a day within the growing season
		and pick a trait from the selector at the right.   Then select GO.
              <br><br>
            </v-card-text>
          </v-card>
        <div v-if="running" xs12 class="text-xs-center mb-4 ml-4 mr-4">
          Running (Job Status {{ job.status }}) ...
        </div>
        <code v-if="!running && job.status === 4" class="mb-4 ml-4 mr-4" style="width: 100%">{{ job.log.join('\n') }}</code>
        <template v-if="!running && job.status === 3">
          <v-card v-if="result.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>Trait Value on Selected Day</v-card-text>
            <json-data-table :data="result" hide-actions/>
          </v-card>
        </template>
      </v-layout>
    </v-layout>
  </v-app>
</template>

<script>
import { utils } from '@girder/components/src';
import { Authentication as GirderAuth } from "@girder/components/src/components";
import { csvParse } from 'd3-dsv';
import scratchFolder from '../scratchFolder';
import pollUntilJobComplete from '../pollUntilJobComplete';
import optionsToParameters from '../optionsToParameters';
import JsonDataTable from '../components/JsonDataTable';

export default {
  name: 'pgls',
  inject: ['girderRest'],
  components: {
    GirderAuth,
    JsonDataTable,
  },
  data: () => ({
    tableFile: {},
    selectedDay: "10",
    selectedTrait: '',
    job: { status: 0 },
    running: false,
    traits: ["canopy_height","leaf_angle_mean","leaf_angle_alpha","leaf_angle_beta","leaf_angle_chi","single_xgboost","abserror_single_xgboost"],
    result: [],
    resultColumns: [],
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRun() {
      return !!(this.selectedDay>0) &&
        !!(this.selectedTrait.length>0); 
    },
    loggedOut() {
      return this.girderRest.user === null;
    },
  },
  methods: {
    async run() {
      this.running = true;
      this.errorLog = null;
      const outname = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

      const params = optionsToParameters({
	// convert the string entered for the day to a number
        selectedDay: Number(this.selectedDay),
        selectedTrait: this.selectedTrait,
        outnameId: outname._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/terraTraitDaily?${params}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.running = false;
        this.result = csvParse((await this.girderRest.get(`item/${outname._id}/download`)).data);
      }
      if (this.job.status === 4) {
        this.running = false;
      }
    },
  }
}
</script>
