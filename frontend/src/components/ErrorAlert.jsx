export default function ErrorAlert({ error, type = 'error' }) {
  if (!error) return null;
  return (
    <div className={`alert alert-${type}`}>
      <strong>{type === 'info' ? 'Bilgi:' : 'Error:'}</strong> {error}
    </div>
  );
}
