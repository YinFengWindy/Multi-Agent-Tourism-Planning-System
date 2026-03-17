<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    size?: number
  }>(),
  {
    size: 44,
  },
)

const logoStyle = computed(() => ({
  '--logo-size': `${props.size}px`,
}))
</script>

<template>
  <span class="brand-logo" :style="logoStyle" aria-hidden="true">
    <svg class="brand-logo__svg" viewBox="0 0 64 64" fill="none">
      <circle class="brand-logo__orbit" cx="32" cy="32" r="20" pathLength="100" />
      <circle class="brand-logo__node" cx="47" cy="19" r="3.5" />
      <path
        class="brand-logo__pin"
        d="M32 17.5C25.65 17.5 20.5 22.65 20.5 29C20.5 37.84 29.47 44.68 31.53 46.15C31.81 46.35 32.19 46.35 32.47 46.15C34.53 44.68 43.5 37.84 43.5 29C43.5 22.65 38.35 17.5 32 17.5Z"
      />
      <path
        class="brand-logo__spark"
        d="M32 24.5L34.15 28.35L38 30.5L34.15 32.65L32 36.5L29.85 32.65L26 30.5L29.85 28.35L32 24.5Z"
      />
    </svg>
  </span>
</template>

<style scoped>
.brand-logo {
  --logo-size: 44px;

  width: var(--logo-size);
  height: var(--logo-size);
  display: inline-grid;
  place-items: center;
  border-radius: calc(var(--logo-size) * 0.34);
  border: 1px solid rgba(255, 255, 255, 0.16);
  background:
    radial-gradient(circle at 28% 24%, rgba(255, 255, 255, 0.32), transparent 32%),
    linear-gradient(145deg, var(--accent), var(--accent-strong));
  box-shadow:
    0 14px 30px rgba(var(--accent-rgb), 0.24),
    inset 0 1px 0 rgba(255, 255, 255, 0.24);
}

.brand-logo__svg {
  width: 78%;
  height: 78%;
}

.brand-logo__orbit {
  stroke: rgba(248, 251, 255, 0.72);
  stroke-width: 3.4;
  stroke-linecap: round;
  stroke-dasharray: 72 28;
  transform: rotate(-28deg);
  transform-origin: center;
}

.brand-logo__node {
  fill: #ffd86a;
}

.brand-logo__pin {
  stroke: #f8fbff;
  stroke-width: 3.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.brand-logo__spark {
  fill: #9be7ff;
}

:global(html[data-theme='light']) .brand-logo {
  border-color: rgba(15, 23, 42, 0.08);
  box-shadow:
    0 14px 28px rgba(38, 58, 94, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.46);
}

:global(html[data-theme='light']) .brand-logo__orbit {
  stroke: rgba(15, 33, 56, 0.22);
}

:global(html[data-theme='light']) .brand-logo__pin {
  stroke: #102035;
}

:global(html[data-theme='light']) .brand-logo__spark {
  fill: #1d5f94;
}
</style>
