<template>
  <v-app>
    <v-content>
      <v-container class="pa-0" fill-height fluid>
        <v-layout fill-height>
          <v-flex xs4>
            <v-dialog v-model="dialog">
              <template v-slot:activator="{ on }">
                <v-btn class="text-none" outline block v-on="on">{{ item ? item.name : 'SELECT DATA' }}</v-btn>
              </template>
              <v-card>
                <v-card-title class="headline">Select nested-json tree file</v-card-title>
                  <GirderDataBrowser
                    ref="dataBrowser"
                    v-if="location"
                    :select-enabled="false"
                    :location.sync="location"
                    :new-item-enabled="false"
                    :new-folder-enabled="false"
                    @itemclick="itemClicked"
                  />
              </v-card>
            </v-dialog>
            <svg>
              <circle v-for="(d, i) in legend" :key="i" cx="20" :cy="20*i + 20" r="8" stroke-width="1" stroke="black" stroke-opacity="0.5" :fill="d.color"/>
              <text v-for="(d, i) in legend" :key="i" x="35" :y="20*i + 20 + 4">{{ d.value }}</text>
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
  </v-app>
</template>

<script>

import { DataBrowser as GirderDataBrowser } from "@girder/components/src/components";
import { scaleOrdinal } from 'd3-scale';
import { schemeCategory10 } from 'd3-scale-chromatic';

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
        fillOpacity: 1,
        strokeColor: 'black',
        strokeWidth: 1,
        strokeOpacity: 0.5,
        radius: 8,
      },
    },
    legend: [],
  }),
  async created() {
    var { data: users } = await this.girderRest.get("user");
    this.location = users[0];
  },
  mounted() {
    var interactorOptions = this.$refs.mapViewport.$geojsMap.interactor().options();
    interactorOptions.keyboard.focusHighlight = false;
    this.$refs.mapViewport.$geojsMap.interactor().options(interactorOptions);
  },
  methods: {
    visit(node) {
      if (node.node_data.attributes) {
        console.log(node.node_data);
        const newLocations = [];
        for (let i = 0; i < node.node_data.attributes.length; ++i) {
          newLocations.push({
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
          this.visit(node.children[i]);
        }
      }
    },
    async itemClicked(item) {
      this.dialog = false;
      this.item = item;
      this.tree = (await this.girderRest.get(`item/${item._id}/download`)).data;
      this.locations = [];
      this.visit(this.tree);
      const colorScale = scaleOrdinal(schemeCategory10);
      this.geojson.features = this.locations.map(d => ({
        type: 'Feature',
        properties: {
          fillColor: colorScale(d.attributes.species),
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
          color: range[i],
        });
      }
    },
  },
}
</script>
<style>
.map:focus {
  outline: none;
}
</style>
