<template>
  <v-app>
    <v-layout class="transform-view" row fill-height>
      <v-navigation-drawer permanent fixed style="width: 400px; min-width: 400px;">
        <v-toolbar dark flat color="primary">
          <v-toolbar-title class="white--text">PGLS</v-toolbar-title>
          <v-spacer/>
          {{ girderRest.user ? girderRest.user.login : '' }}
          <v-btn flat icon @click="girderRest.logout()">
            <v-icon>$vuetify.icons.logout</v-icon>
          </v-btn>
          <v-dialog :value="loggedOut" persistent full-width max-width="600px">
            <girder-auth
              :register="false"
              :key="girderRest.token"
              :forgot-password-url="forgotPasswordUrl"
            />
          </v-dialog>
        </v-toolbar>
        <v-container fluid>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.tableFile.click()'>{{ tableFileName || 'UPLOAD TABLE' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="tableFile"
              @change="uploadTable($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-btn class="text-none" outline block @click='$refs.treeFile.click()'>{{ treeFileName || 'UPLOAD TREE' }}</v-btn>
            <input
              type="file"
              style="display: none"
              ref="treeFile"
              @change="uploadTree($event.target.files[0])"
            >
          </v-flex>
          <v-flex xs12>
            <v-select label="Correlation" v-model="correlation" :items="correlationOptions" />
          </v-flex>
          <v-flex xs12>
            <v-select label="Independent Variable" v-model="independentVariable" :items="columns" />
          </v-flex>
          <v-flex xs12>
            <v-select label="Dependent Variable" v-model="dependentVariable" :items="columns" />
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
              <b>PGLS (Phylogenetic generalized least squares)</b> is a method for testing for correlations of
              two continuously distributed characters that vary across species. For example, one might be interested in
              the correlation between body size (X) and metabolic rate (Y).
              <br><br>
              The phylogenetic tree is used to account for the fact that species are not independent data points. In this
              case, the tree is used to <b>explain correlations in the residuals</b> from the regression line of Y against X.
              <br><br>
              In this app, you can model the residuals under three models: Brownian motion (BM), a random-walk model common
              for comparative methods; Ornstein-Uhlenbeck (OU), a model where divergence is constrained away from some optimal value,
              in this case the regression line itself; and Pagel's lambda, a model that rescales the tree to effectively
              change the rate of divergence through time.
              <br><br>
              When you carry out this analysis, you are assuming that both the species values and the tree are <b>known without error</b>,
              that the relationship between X and Y can be described with a <b>straight line</b>, and that the <b>model you select is reasonable</b>
              as a description of how residuals from that line change through time.
              <br><br>
              1. Upload your table (.csv) and tree (Newick, .phy).
              <br><br>
              2. Select the desired correlation mode, and independent and dependent variables.
              <br><br>
              3. Click GO.
            </v-card-text>
          </v-card>
          <v-card v-if="table.length > 0" class="mb-4 ml-4 mr-4">
            <v-card-text>{{ tableFileName }}</v-card-text>
            <json-data-table :data="table" />
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
          <v-card class="mb-4 ml-4 mr-4">
            <v-card-text>Correlation plot</v-card-text>
            <img :src="plotUrl" style="display: block; margin: auto">
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
    table: [],
    treeFile: {},
    tableFileName: '',
    treeFileName: '',
    job: { status: 0 },
    running: false,
    columns: [],
    correlation: 'BM',
    correlationOptions: ['BM', 'OU', 'lambda'],
    independentVariable: null,
    dependentVariable: null,
    result: [],
    resultColumns: [],
    plotUrl: '',
    forgotPasswordUrl: null,
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  computed: {
    readyToRun() {
      return !!this.treeFileName &&
        !!this.tableFileName &&
        !!this.independentVariable &&
        !!this.dependentVariable;
    },
    loggedOut() {
      return this.girderRest.user === null;
    },
  },
  methods: {
    async run() {
      this.running = true;
      this.errorLog = null;
      const modelFitSummaryItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data
      const plotItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data

      const params = optionsToParameters({
        tableFileId: this.tableFile._id,
        treeFileId: this.treeFile._id,
        correlation: this.correlation,
        independentVariable: this.independentVariable,
        dependentVariable: this.dependentVariable,
        modelFitSummaryItemId: modelFitSummaryItem._id,
        plotItemId: plotItem._id,
      });
      this.job = (await this.girderRest.post(
        `arbor_nova/pgls?${params}`,
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
    async uploadTable(file) {
      if (file) {
        this.tableFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent: this.scratchFolder});
        this.tableFile = await uploader.start();
        const reader = new FileReader();
        reader.addEventListener('loadend', e => {
          const text = e.srcElement.result;
          this.table = csvParse(text);
          this.columns = csvParse(text).columns;
        });
        reader.readAsText(file);
      }
    },
    async uploadTree(file) {
      if (file) {
        this.treeFileName = file.name;
        const uploader = new utils.Upload(file, {$rest: this.girderRest, parent:this.scratchFolder});
        this.treeFile = await uploader.start();
      }
    },
  }
}
</script>
