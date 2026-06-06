// frontend/src/components/ComingSoon.jsx
//
// Lightweight placeholder for menu items whose role-scoped pages aren't built
// yet (Sprint 4.5, Chunk 5). Keeps the per-role menus complete with no dead
// links; Layer 2 swaps these routes for real scoped pages one at a time.

export default function ComingSoon({ title }) {
  return (
    <div className="p-6">
      <div className="text-lg font-bold mb-md">{title || "Section"}</div>
      <div className="hint">This section is coming soon.</div>
    </div>
  );
}
