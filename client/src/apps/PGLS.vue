<template>
  <div>
    <div>
      Table: <input type="file" @change="uploadTable($event.target.files[0])">
    </div>
    <div>
      Tree: <input type="file" @change="uploadTree($event.target.files[0])">
    </div>
    <div>
      Correlation:
      <select v-model="correlation">
        <option>BM</option>
        <option>OU</option>
        <option>lambda</option>
      </select>
    </div>
    <div>
      Independent Variable:
      <select v-model="independentVariable">
        <option v-for="col in columns" v-bind:key="col">{{ col }}</option>
      </select>
    </div>
    <div>
      Dependent Variable:
      <select v-model="dependentVariable">
        <option v-for="col in columns" v-bind:key="col">{{ col }}</option>
      </select>
    </div>
    <div>
      <button @click="run">Run</button>
    </div>
    <div>Job status: {{ job.status }}</div>
    <div>{{ result }}</div>
    <img :src="plotUrl">
  </div>
</template>

<script>
import { utils } from '@girder/components/src';
import { csvParse } from 'd3-dsv';
import scratchFolder from '../scratchFolder';
import pollUntilJobComplete from '../pollUntilJobComplete';
import optionsToParameters from '../optionsToParameters';

export default {
  name: 'pgls',
  inject: ['girderRest'],
  data: () => ({
    tableFile: {},
    treeFile: {},
    job: { status: 0 },
    result: '',
    plotUrl: '',
    columns: [],
    correlation: 'BM',
    independentVariable: null,
    dependentVariable: null,
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  methods: {
    async run() {
      const modelFitSummaryItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data;
      const plotItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data;
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
        this.result = (await this.girderRest.get(`item/${modelFitSummaryItem._id}/download`)).data;
        this.plotUrl = `${this.girderRest.apiRoot}/item/${plotItem._id}/download`;
      }
    },
    async uploadTable(file) {
      const uploader = new utils.Upload(this.girderRest, file, this.scratchFolder);
      this.tableFile = await uploader.start();
      const reader = new FileReader();
      reader.addEventListener('loadend', e => {
        const text = e.srcElement.result;
        this.columns = csvParse(text).columns;
      });
      reader.readAsText(file);
    },
    async uploadTree(file) {
      const uploader = new utils.Upload(this.girderRest, file, this.scratchFolder);
      this.treeFile = await uploader.start();
    },
  }
}
</script>
