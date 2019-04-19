<template>
  <div>
    <input type="file" @change="upload($event.target.files[0])">
    <button @click="run">Run</button>
    <div>Job status: {{ job.status }}</div>
    <div>{{ result }}</div>
  </div>
</template>

<script>
import { utils } from '@girder/components/src';
import scratchFolder from '../scratchFolder';
import pollUntilJobComplete from '../pollUntilJobComplete';

export default {
  name: 'append-column',
  inject: ['girderRest'],
  data: () => ({
    inputFile: {},
    job: { status: 0 },
    result: '',
  }),
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  methods: {
    async run() {
      const resultItem = (await this.girderRest.post(
        `item?folderId=${this.scratchFolder._id}&name=result`,
      )).data;
      this.job = (await this.girderRest.post(
        `arbor_nova/csvColumnAppend?fileId=${this.inputFile._id}&itemId=${resultItem._id}`,
      )).data;

      await pollUntilJobComplete(this.girderRest, this.job, job => this.job = job);

      if (this.job.status === 3) {
        this.result = (await this.girderRest.get(`item/${resultItem._id}/download`)).data;
      }
    },
    async upload(file) {
      const uploader = new utils.Upload(this.girderRest, file, this.scratchFolder);
      this.inputFile = await uploader.start();
    }
  }
}
</script>
