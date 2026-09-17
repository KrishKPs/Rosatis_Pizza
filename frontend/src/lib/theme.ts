// Mirrors the CSS custom properties in index.css. Recharts renders raw SVG
// attributes in places that don't resolve CSS variables, so chart colors are
// duplicated here as plain hex — everything else should use the CSS vars.
export const theme = {
  bg: "#121316",
  surface1: "#191b1f",
  surface2: "#212329",
  surface3: "#2a2d34",
  border: "#2e3038",
  textPrimary: "#edeef0",
  textSecondary: "#999da6",
  textTertiary: "#6b6f79",
  accent: "#e0912f",
  accentDim: "#a86a24",
  profit: "#56a76b",
  loss: "#e2483d",
};

export const CATEGORY_COLORS = [
  "#e0912f",
  "#56a76b",
  "#5b8ec4",
  "#c26bd4",
  "#d4b53f",
  "#4fb0a3",
  "#e2483d",
  "#8a8fd6",
  "#b98653",
];
