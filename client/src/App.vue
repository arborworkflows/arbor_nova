<template>
  <div id="app">
    <input type="file" @change="upload($event.target.files[0])">
    <button @click="run">Run</button>
    <div>{{ JSON.stringify(inputFile) }}</div>
    <div>{{ JSON.stringify(job) }}</div>
    <div>{{ result }}</div>
  </div>
</template>

<script>
import { utils } from '@girder/components/src';

export default {
  name: 'app',
  inject: ['girderRest'],
  data: () => ({
    inputFile: {},
    job: {},
    result: '',
  }),
  asyncComputed: {
    async me() {
      return (await this.girderRest.get('user/me')).data;
    },
    async scratchFolder() {
      const me = (await this.girderRest.get('user/me')).data;
      const folders = (await this.girderRest.get(`folder?parentId=${me._id}&parentType=user`)).data;
      return folders.filter(folder => folder.name === 'Private')[0];
    }
  },
  methods: {
    async run() {
      try {
        const resultItem = (await this.girderRest.post(
          `item?folderId=${this.scratchFolder._id}&name=result`,
        )).data;
        this.job = (await this.girderRest.post(
          `arbor_nova/csvColumnAppend?fileId=${this.inputFile._id}&itemId=${resultItem._id}`,
        )).data;

        // INACTIVE = 0
        // QUEUED = 1
        // RUNNING = 2
        // SUCCESS = 3
        // ERROR = 4
        // CANCELED = 5
        const delay = t => new Promise(resolve => {
          setTimeout(resolve, t);
        });
        const finalStates = [3, 4, 5];
        while (finalStates.indexOf(this.job.status) === -1) {
          await delay(500);
          this.job = (await this.girderRest.get(`job/${this.job._id}`)).data;
        }

        if (this.job.status === 3) {
          this.result = (await this.girderRest.get(`item/${resultItem._id}/download`)).data;
        }
      } catch (err) {
        console.log(err);
      }
    },
    async upload(file) {
      const uploader = new utils.Upload(this.girderRest, file, this.scratchFolder);
      this.inputFile = await uploader.start();
    }
  }
}
</script>
