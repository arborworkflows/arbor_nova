<template>
  <v-app>
    <v-content>
      <v-container class="pa-0" fill-height fluid>
        <v-layout fill-height>
          <v-flex xs4 ref="treeContainer">
            <svg height="100%" width="100%" :key="treeUpdateKey">
              <g>
                <line
                  v-for="(d, i) in edges"
                  :key="i"
                  :x1="heightScale(d.height1)"
                  :y1="positionScale(d.position1)"
                  :x2="heightScale(d.height2)"
                  :y2="positionScale(d.position2)"
                  stroke-width="0.5"
                  stroke="black"
                />
              </g>
              <g>
                <circle
                  v-for="(d, i) in nodes"
                  :key="i"
                  :cx="heightScale(d.height)"
                  :cy="positionScale(d.position)"
                  r="4"
                  stroke-width="1"
                  stroke="black"
                  stroke-opacity="0.5"
                  :fill="colorScale(d.position)"
                  :opacity="d.visible ? 1 : 0.2"
                  @click="nodeClick(d)"
                >
                  <title>{{ d.name }}</title>
                </circle>
              </g>
            </svg>
          </v-flex>
          <v-flex fill-height xs8>
            <geojs-map-viewport
              ref="mapViewport"
              class="map"
            >
              <geojs-tile-layer
                :url='url'
                :attribution='attribution'
                :opacity='opacity'
                :zIndex='0'
              />
              <geojs-geojson-layer
                :featureStyle='featureStyle'
                :geojson='geojson'
                :opacity='1'
                :zIndex='1'
              />
            </geojs-map-viewport>
          </v-flex>
        </v-layout>
      </v-container>
    </v-content>
    <v-dialog v-model="dialog" full-width max-width="600px">
      <template v-slot:activator="{ on }">
        <v-btn class="data-button text-none primary" flat absolute v-on="on">{{ item ? item.name : 'SELECT DATA' }}</v-btn>
      </template>
      <v-card>
        <v-card-title class="headline">Select nested-json tree file</v-card-title>
          <GirderDataBrowser
            ref="dataBrowser"
            v-if="location"
            :location.sync="location"
            :no-selection
            :no-upload
            :no-new-folder
            @itemclick="itemClicked"
          />
      </v-card>
    </v-dialog>
    <v-select
      v-if="traits"
      class="trait-select"
      solo
      v-model="trait"
      :items="traits"
    />
    <div v-if="legend.length > 0" class="legend grey lighten-3">
      <svg :height="legend.length * 20 + 20 - 4" width="200">
        <circle
          v-for="(d, i) in legend"
          :key="i"
          cx="20"
          :cy="20*i + 20"
          r="8"
          stroke-width="1"
          stroke="black"
          stroke-opacity="0.5"
          :fill="d.color"
        />
        <text
          v-for="(d, i) in legend"
          :key="i"
          x="35"
          :y="20*i + 20 + 5"
        >
          {{ d.value }}
        </text>
      </svg>
    </div>
  </v-app>
</template>

<script>

import { DataBrowser as GirderDataBrowser } from "@girder/components/src/components";
import { scaleOrdinal, scaleSequential } from 'd3-scale';
import { schemeCategory10, schemePaired, interpolateWarm } from 'd3-scale-chromatic';
import scratchFolder from '../scratchFolder';

export default {
  name: 'phylo-map',
  inject: ['girderRest'],
  components: {
    GirderDataBrowser,
  },
  data: () => ({
    location: null,
    dialog: false,
    item: null,
    tree: {},
    opacity: 1,
    url: 'http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
    attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
    locations: [],
    geojson: {
      type: 'FeatureCollection',
      features: [],
    },
    featureStyle: {
      point: {
        strokeColor: 'black',
        strokeWidth: 1,
        radius: 4,
      },
    },
    nodes: [],
    edges: [],
    legend: [],
    maxHeight: 0,
    maxPosition: 0,
    treeUpdateKey: 0,
    trait: 'species',
    traits: null,
  }),
  async created() {
    await scratchFolder(this.girderRest);
    this.location = {...this.girderRest.user};
  },
  asyncComputed: {
    scratchFolder() {
      return scratchFolder(this.girderRest);
    },
  },
  mounted() {
    var interactorOptions = this.$refs.mapViewport.$geojsMap.interactor().options();
    interactorOptions.keyboard.focusHighlight = false;
    this.$refs.mapViewport.$geojsMap.interactor().options(interactorOptions);
  },
  watch: {
    trait() {
      this.generateGeoJson();
    }
  },
  methods: {
    layoutTree() {
      let leafIndex = 0;
      this.nodes = [];
      this.edges = [];
      const visit = (node) => {
        this.nodes.push(node);
        node.visible = true;
        if (node.children) {
          node.position = 0;
          node.height = 0;
          node.species = [];
          node.childCount = 0;
          for (let i = 0; i < node.children.length; i++) {
            visit(node.children[i]);
            node.childCount += node.children[i].childCount;
            node.position += node.children[i].childCount * node.children[i].position;
            if (node.children[i].height + 1 > node.height) {
              node.height = node.children[i].height + 1;
            }
            node.species = [...node.species, ...node.children[i].species];
          }
          node.name = node.species.join(', ');
          node.position /= node.childCount;
          for (let i = 0; i < node.children.length; i++) {
            this.edges.push({
              position1: node.position,
              height1: node.height,
              position2: node.children[i].position,
              height2: node.height,
            });
            this.edges.push({
              position1: node.children[i].position,
              height1: node.height,
              position2: node.children[i].position,
              height2: node.children[i].height,
            });
          }
        } else {
          node.position = leafIndex;
          node.height = 0;
          node.childCount = 1;
          node.species = [node.node_data['node name']];
          node.name = node.species[0];
          leafIndex += 1;
        }
      }
      visit(this.tree);
      this.maxPosition = leafIndex - 1;
      this.maxHeight = this.tree.height;
    },
    extractOccurrences() {
      this.locations = [];
      const visit = (node) => {
        if (node.node_data.attributes) {
          const newLocations = [];
          for (let i = 0; i < node.node_data.attributes.length; ++i) {
            this.traits = Object.keys(node.node_data.attributes[i]);
            newLocations.push({
              node,
              attributes: node.node_data.attributes[i],
              loc: [
                node.node_data.attributes[i].long,
                node.node_data.attributes[i].lat,
              ],
            });
          }
          this.locations = [...this.locations, ...newLocations];
        }
        if (node.children) {
          for (let i = 0; i < node.children.length; i++) {
            visit(node.children[i]);
          }
        }
      };
      visit(this.tree);
    },
    generateGeoJson() {
      this.legend = [];
      if (this.trait === 'species') {
        const speciesFound = {};
        this.geojson.features = this.locations.map(d => {
          const color = this.colorScale(d.node.position);
          const species = d.attributes.species;
          if (!speciesFound[species]) {
            this.legend.push({
              value: species,
              color,
            });
            speciesFound[species] = true;
          }
          return {
            type: 'Feature',
            properties: {
              fillColor: color,
              fillOpacity: d.node.visible ? 1 : 0,
              strokeOpacity: d.node.visible ? 0.5 : 0,
            },
            geometry: {
              type: 'Point',
              coordinates: d.loc,
            },
          };
        });
      } else {
        const colorScale = scaleOrdinal(schemePaired);
        this.geojson.features = this.locations.map(d => ({
            type: 'Feature',
            properties: {
              fillColor: colorScale(d.attributes[this.trait]),
              fillOpacity: d.node.visible ? 1 : 0,
              strokeOpacity: d.node.visible ? 0.5 : 0,
            },
            geometry: {
              type: 'Point',
              coordinates: d.loc,
            },
        }));
        const domain = colorScale.domain();
        const range = colorScale.range();
        this.legend = [];
        for (let i = 0; i < domain.length; i++) {
          this.legend.push({
            value: domain[i],
            color: range[i % range.length],
          });
        }
      }
    },
    positionScale(position) {
      return position * (this.$refs.treeContainer.clientHeight - 20) / this.maxPosition + 10;
    },
    heightScale(height) {
      return this.$refs.treeContainer.clientWidth - (height * (this.$refs.treeContainer.clientWidth - 20) / this.maxHeight + 10);
    },
    colorScale(position) {
      return interpolateWarm(position/this.maxPosition);
    },
    async itemClicked(item) {
      this.dialog = false;
      this.item = item;
      this.tree = (await this.girderRest.get(`item/${item._id}/download`)).data;
      this.layoutTree();
      this.extractOccurrences();
      this.generateGeoJson();
    },
    nodeClick(node) {
      const newVisible = !node.visible;
      const visit = (node) => {
        node.visible = newVisible;
        if (node.children) {
          for (let i = 0; i < node.children.length; i++) {
            visit(node.children[i]);
          }
        }
      };
      visit(node);
      this.generateGeoJson();
      // Force update of tree since nodes have changed
      this.treeUpdateKey += 1;
    }
  },
}
</script>
<style>
.map:focus {
  outline: none;
}
.data-button {
  top: 20px;
  left: 20px;
}
.trait-select {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}
.legend {
  position: absolute;
  top: 100px;
  right: 20px;
  border-radius: 10px;
  z-index: 10;
}
</style>
