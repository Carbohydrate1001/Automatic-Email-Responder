<template>
  <div id="app">
    <AppHeader v-if="showHeader" />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'

const route = useRoute()
const showHeader = computed(() => route.name !== 'Login')
</script>
