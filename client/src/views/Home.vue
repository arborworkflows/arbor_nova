<template>
<v-app>
  <div class="grey lighten-3 root">
    <v-container
      grid-list-xl
    >
      <v-layout row wrap>
        <v-flex xs12 class="text-xs-center">
          <img src="../assets/FNLCR-logo.png">
        </v-flex>
        <v-flex xs12>
          <span class="title">Applications</span>
        </v-flex>
        <v-flex
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
export default {
  name: 'home',
  data: () => ({
    smallScreen: false,
    samples: [
//      {
//        label: 'Phylogenetic generalized least squares (PGLS)',
//        image: require('../assets/pgls.png'),
//        route: 'pgls',
//        description: 'A method for testing for correlations of two continuously distributed characters that vary across species.',
//      },
//      {
//        label: 'PhyloMap',
//        image: require('../assets/phylomap.png'),
//        route: 'phylomap',
//        description: 'Explore a phylogenetic tree and associated species location data.',
//      },
//      {   
//        label: 'Ancestral State Reconstruction',
//        image: require('../assets/asr.png'),
//        route: 'asr',
//        description: 'Explore the ancestral signal of a particular character across the tree',
//      },    
//      {   
//        label: 'PolyA tail',
//        image: require('../assets/polya.png'),
//        route: 'polya',
//        description: 'Search for Polyadenylation tails',
//      },    
//      {   
//        label: 'Blastn',
//        image: require('../assets/blastn.png'),
//        route: 'blastn',
//        description: 'Search similarity between FASTA files',
//      },    
//      {   
//        label: 'DNN Infer',
//        image: require('../assets/infer.png'),
//        route: 'infer',
//        description: 'Perform forward inferencing using a pretrained U-Net network',
//      },    
//      {   
//        label: 'Docker PolyA tail',
//        image: require('../assets/docker_polya.png'),
//        route: 'docker_polya',
//        description: 'Search for PolyA tails via docker',
//      },    
      {   
        label: 'Rhabdo Segmentation',
        image: require('../assets/infer_rhabdo.png'),
        route: 'infer_rhabdo',
        description: 'Segment an H&E-stained Rhabdomyosarcoma image',
      },    
    ],
  }),
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
  background: rgba(0,0,0,0.4);
  padding: 10px;
}
</style>
