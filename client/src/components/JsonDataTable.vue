<template>
<v-data-table
  :headers="data.columns.map(d => ({text: d, value: d}))"
  :items="data"
  :hide-actions="hideActions"
>
  <template v-slot:items="props">
    <td v-for="column in data.columns" v-bind:key="column">
      {{ props.item[column] }}
    </td>
  </template>
</v-data-table>
</template>
<script>
export default {
  name: 'json-data-table',
  props: ['data', 'hide-actions'],
};
</script>
