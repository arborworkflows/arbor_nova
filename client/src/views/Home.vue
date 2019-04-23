<template>
<v-app>
  <div class="grey lighten-3 root">
    <v-container
      grid-list-xl
    >
      <v-layout row wrap>
        <v-flex xs12 class="text-xs-center">
          <img src="arbor_128px.png">
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
  <!-- <div>
    <router-link to="/appendcolumn">Append Column</router-link>
    <router-link to="/pgls">PGLS</router-link>
  </div> -->
</v-app>
</template>

<script>
export default {
  name: 'home',
  data: () => ({
    smallScreen: false,
    samples: [
      {
        label: 'Phylogenetic generalized least squares (PGLS)',
        image: 'pgls.png',
        route: 'pgls',
        description: 'A method for testing for correlations of two continuously distributed characters that vary across species.',
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
