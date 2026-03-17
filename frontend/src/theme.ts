export type ThemeMode = 'dark' | 'light'

export interface ThemePreset {
  id: string
  label: string
  accent: string
}

export const themePresets: ThemePreset[] = [
  { id: 'aurora', label: '极光蓝', accent: '#4f8cff' },
  { id: 'emerald', label: '森林绿', accent: '#18b87a' },
  { id: 'sunset', label: '落日橙', accent: '#ff8c42' },
  { id: 'violet', label: '极夜紫', accent: '#7c5cff' },
  { id: 'rose', label: '玫瑰红', accent: '#ff5f8f' },
]

const STORAGE_KEYS = {
  mode: 'mtp-theme-mode',
  accent: 'mtp-theme-accent',
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function normalizeHexColor(input: string) {
  const cleaned = input.trim().replace('#', '')
  if (/^[0-9a-fA-F]{3}$/.test(cleaned)) {
    return `#${cleaned
      .split('')
      .map((char) => `${char}${char}`)
      .join('')}`.toLowerCase()
  }
  if (/^[0-9a-fA-F]{6}$/.test(cleaned)) {
    return `#${cleaned}`.toLowerCase()
  }
  return '#4f8cff'
}

function hexToRgb(hex: string) {
  const normalized = normalizeHexColor(hex).replace('#', '')
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  }
}

function rgbToHex(red: number, green: number, blue: number) {
  return `#${[red, green, blue]
    .map((channel) => clamp(Math.round(channel), 0, 255).toString(16).padStart(2, '0'))
    .join('')}`
}

function tint(hex: string, amount: number) {
  const { r, g, b } = hexToRgb(hex)
  return rgbToHex(r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount)
}

function shade(hex: string, amount: number) {
  const { r, g, b } = hexToRgb(hex)
  return rgbToHex(r * (1 - amount), g * (1 - amount), b * (1 - amount))
}

function getContrastColor(hex: string) {
  const { r, g, b } = hexToRgb(hex)
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
  return luminance > 0.6 ? '#08111f' : '#f7fbff'
}

export function getStoredTheme() {
  if (typeof window === 'undefined') {
    return { mode: 'light' as ThemeMode, accent: '#4f8cff' }
  }

  const storedMode = window.localStorage.getItem(STORAGE_KEYS.mode)
  const storedAccent = window.localStorage.getItem(STORAGE_KEYS.accent)
  const mode: ThemeMode = storedMode === 'dark' ? 'dark' : 'light'
  return {
    mode,
    accent: normalizeHexColor(storedAccent ?? themePresets[0].accent),
  }
}

export function applyTheme(mode: ThemeMode, accent: string) {
  if (typeof document === 'undefined') {
    return
  }

  const normalizedAccent = normalizeHexColor(accent)
  const accentRgb = hexToRgb(normalizedAccent)
  const root = document.documentElement
  root.dataset.theme = mode
  root.style.setProperty('--accent', normalizedAccent)
  root.style.setProperty('--accent-rgb', `${accentRgb.r}, ${accentRgb.g}, ${accentRgb.b}`)
  root.style.setProperty('--accent-soft', tint(normalizedAccent, mode === 'light' ? 0.82 : 0.18))
  root.style.setProperty('--accent-muted', tint(normalizedAccent, mode === 'light' ? 0.9 : 0.28))
  root.style.setProperty('--accent-strong', shade(normalizedAccent, mode === 'light' ? 0.14 : 0.22))
  root.style.setProperty('--accent-contrast', getContrastColor(normalizedAccent))
  window.localStorage.setItem(STORAGE_KEYS.mode, mode)
  window.localStorage.setItem(STORAGE_KEYS.accent, normalizedAccent)
}

export function normalizeThemeColor(value: string) {
  return normalizeHexColor(value)
}
