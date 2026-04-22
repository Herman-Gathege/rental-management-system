// frontend/src/components/Modal.jsx
export default function Modal({ title, children, onClose }) {
  return (
    <div className="modal-backdrop">
      <div className="modal-card">
        <header className="flex justify-between items-center mb-md">
          <h3 className="text-lg text-bold">{title}</h3>
          <button className="btn-ghost" onClick={onClose}>✕</button>
        </header>

        {children}
      </div>
    </div>
  );
}
