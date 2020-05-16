<template>
<v-app>
  <div class="grey lighten-3 root">
    <v-container
      grid-list-xl
    >
      <v-layout row wrap>
        <v-flex xs12 class="text-xs-center">
          <img src="../assets/darpa-purdue-logo.png">
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
      {
        label: 'Explore Sensor Collected Traits',
        image: require('../assets/terra_trait.png'),
        route: 'terratrait',
        description: 'Provide a day-by-day exploration of trait values across all cultivars',
      },
      {
        label: 'Train a Model on Season 4 or 6 Data',
        image: require('../assets/terra_sorghum.png'),
        route: 'terramodel',
        description: 'Fit a new model to observed trait measurements',
      },
      {
        label: 'Explore Pairwise Trait Correlation',
        image: require('../assets/trait_correlation.png'),
        route: 'terrascatter',
        description: 'Scatterplot between two trait measurements',
      },
      {
        label: 'Compare Trait differences across Cultivars',
        image: require('../assets/cultivar_matrix.png'),
        route: 'cultivarmatrix',
        description: 'Plot specific trait differences across all the cultivars',
      },
      {
        label: 'Explore a Single Cultivar',
        image: require('../assets/explore_single_cultivar.png'),
        route: 'explorecultivar',
        description: 'Explore the measurements of a single cultivar',
      },
      //{
      //  label: 'PhyloMap',
      //  image: require('../assets/phylomap.png'),
      //  route: 'phylomap',
      //  description: 'Explore the phylogenetic tree and the associated cultivar location data.',
      //},
      //{   
      //  label: 'Ancestral State Reconstruction',
      //  image: require('../assets/asr.png'),
      //  route: 'asr',
      //  description: 'Explore the ancestral signal of a particular character across the tree',
      //},    
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
