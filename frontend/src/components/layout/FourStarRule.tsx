// The one Chicago-flag nod in the whole app: four six-pointed stars, used only
// here, under the store name — not repeated as decoration anywhere else.
export function FourStarRule() {
  const star = (key: number) => (
    <svg key={key} width="10" height="10" viewBox="0 0 24 24" fill="var(--accent)">
      <path d="M12 0l2.2 6.6 6.9.4-5.4 4.3 2 6.7-5.7-4-5.7 4 2-6.7-5.4-4.3 6.9-.4z" />
    </svg>
  );
  return <div className="flex gap-2 opacity-80">{[0, 1, 2, 3].map(star)}</div>;
}
