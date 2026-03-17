import { createRouter, createWebHistory } from 'vue-router'

import WorkspaceLayout from './layouts/WorkspaceLayout.vue'
import ExecutionView from './views/ExecutionView.vue'
import OverviewView from './views/OverviewView.vue'
import ResultsView from './views/ResultsView.vue'
import ThemeView from './views/ThemeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: WorkspaceLayout,
      children: [
        { path: '', redirect: { name: 'overview' } },
        { path: 'overview', name: 'overview', component: OverviewView },
        { path: 'execution', name: 'execution', component: ExecutionView },
        { path: 'results', name: 'results', component: ResultsView },
        { path: 'theme', name: 'theme', component: ThemeView },
      ],
    },
  ],
})

export default router
